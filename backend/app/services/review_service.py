import logging
import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import PRReview, Repository
from app.schemas import AIReviewOutput
from app.services import ai_service, github_service, slack_service

logger = logging.getLogger(__name__)


def _score_emoji(score: float) -> str:
    if score >= 80:
        return "✅"
    elif score >= 60:
        return "⚠️"
    return "❌"


def _format_review_comment(
    review: AIReviewOutput,
    pr_number: int,
    benchmark_percentile: float,
) -> str:
    """Build the full markdown comment body for GitHub."""

    def row(label: str, score: float) -> str:
        return f"| {label} | {score:.0f}/100 | {_score_emoji(score)} |"

    critical_section = (
        "\n".join(f"- {issue}" for issue in review.critical_issues)
        if review.critical_issues
        else "_No critical issues found._"
    )

    warnings_section = (
        "\n".join(f"- {warning}" for warning in review.warnings)
        if review.warnings
        else "_No warnings._"
    )

    test_section = (
        "\n".join(f"{i}. {suggestion}" for i, suggestion in enumerate(review.test_suggestions, 1))
        if review.test_suggestions
        else "_No test suggestions._"
    )

    return f"""## 🤖 CodeIntel Review

**Overall Confidence Score: {review.score_overall:.0f}/100 {_score_emoji(review.score_overall)}**

---

### 📊 Dimension Scores

| Dimension | Score | Status |
|-----------|-------|--------|
{row("✅ Requirement Alignment", review.score_requirement)}
{row("🔒 Security", review.score_security)}
{row("🏗️ Code Quality", review.score_quality)}
{row("⚡ Performance", review.score_performance)}

---

### 🚨 Critical Issues

{critical_section}

---

### ⚠️ Warnings

{warnings_section}

---

### 📋 Dimension Feedback

<details>
<summary><strong>✅ Requirement Alignment</strong></summary>

{review.feedback_requirement}
</details>

<details>
<summary><strong>🔒 Security</strong></summary>

{review.feedback_security}
</details>

<details>
<summary><strong>🏗️ Code Quality</strong></summary>

{review.feedback_quality}
</details>

<details>
<summary><strong>⚡ Performance</strong></summary>

{review.feedback_performance}
</details>

---

### 🧪 Suggested Test Cases

{test_section}

---

*CodeIntel AI Review • This PR scored higher than **{benchmark_percentile:.0f}%** of PRs in this repository*
*Re-trigger review by commenting `/codeintel review`*"""


async def _get_or_create_repository(
    session: AsyncSession, repo_full_name: str, installation_id: int = 0
) -> Repository:
    """Fetch existing repo record or create a new one."""
    result = await session.execute(
        select(Repository).where(Repository.full_name == repo_full_name)
    )
    repo = result.scalar_one_or_none()

    if repo is None:
        parts = repo_full_name.split("/", 1)
        owner, name = parts[0], parts[1] if len(parts) > 1 else repo_full_name

        # Try to get GitHub repo ID
        meta = await github_service.get_repo_metadata(repo_full_name, installation_id)

        repo = Repository(
            github_repo_id=meta.get("github_repo_id"),
            full_name=repo_full_name,
            owner=owner,
            name=name,
        )
        session.add(repo)
        await session.flush()
        logger.info("Created new repository record: %s (id=%d)", repo_full_name, repo.id)

    return repo


async def _compute_benchmark(
    session: AsyncSession, repo_id: int, score: float
) -> float:
    """Return the percentile of `score` within this repository's reviews."""
    from sqlalchemy import func

    total_result = await session.execute(
        select(func.count()).where(PRReview.repo_id == repo_id)
    )
    total = total_result.scalar() or 0

    if total == 0:
        return 100.0

    better_result = await session.execute(
        select(func.count()).where(
            PRReview.repo_id == repo_id, PRReview.score_overall < score
        )
    )
    better_count = better_result.scalar() or 0

    percentile = (better_count / total) * 100.0
    return round(percentile, 1)


async def run_pr_review(
    session: AsyncSession,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    installation_id: int = 0,
) -> PRReview:
    """
    Full review pipeline:
    1. Fetch PR data and linked issue
    2. Call AI service
    3. Persist to DB
    4. Post GitHub comment + commit status
    5. Send Slack notification
    """
    logger.info("Starting review pipeline for %s#%d", repo_full_name, pr_number)

    # ── Step 1: Gather data ────────────────────────────────────────────────
    pr_details = await github_service.get_pr_details(repo_full_name, pr_number, installation_id)
    diff = await github_service.get_pr_diff(repo_full_name, pr_number, installation_id)
    linked_issue = await github_service.get_linked_issue(
        repo_full_name, pr_details["body"], installation_id
    )
    repo_meta = await github_service.get_repo_metadata(repo_full_name, installation_id)

    logger.info(
        "Fetched PR data for %s#%d (diff=%d chars, linked_issue=%s)",
        repo_full_name,
        pr_number,
        len(diff),
        f"#{linked_issue['number']}" if linked_issue else "none",
    )

    # ── Step 2: AI Review ─────────────────────────────────────────────────
    ai_result: AIReviewOutput = await ai_service.generate_review(
        diff=diff,
        pr_title=pr_details["title"],
        pr_body=pr_details["body"],
        linked_issue=linked_issue,
        repo_language=repo_meta.get("language", "Unknown"),
        repo_description=repo_meta.get("description", ""),
    )

    # ── Step 3: Persist ───────────────────────────────────────────────────
    repo = await _get_or_create_repository(session, repo_full_name, installation_id)

    # Check if a review for this exact sha already exists
    existing_result = await session.execute(
        select(PRReview).where(
            PRReview.repo_id == repo.id,
            PRReview.pr_number == pr_number,
            PRReview.head_sha == head_sha,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing review
        existing.score_overall = ai_result.score_overall
        existing.score_requirement = ai_result.score_requirement
        existing.score_security = ai_result.score_security
        existing.score_quality = ai_result.score_quality
        existing.score_performance = ai_result.score_performance
        existing.feedback_requirement = ai_result.feedback_requirement
        existing.feedback_security = ai_result.feedback_security
        existing.feedback_quality = ai_result.feedback_quality
        existing.feedback_performance = ai_result.feedback_performance
        existing.critical_issues = ai_result.critical_issues
        existing.warnings = ai_result.warnings
        existing.test_suggestions = ai_result.test_suggestions
        pr_review = existing
        logger.info("Updated existing review id=%d for %s#%d", existing.id, repo_full_name, pr_number)
    else:
        pr_review = PRReview(
            repo_id=repo.id,
            pr_number=pr_number,
            pr_title=pr_details["title"],
            pr_author=pr_details["author"],
            head_sha=head_sha,
            score_overall=ai_result.score_overall,
            score_requirement=ai_result.score_requirement,
            score_security=ai_result.score_security,
            score_quality=ai_result.score_quality,
            score_performance=ai_result.score_performance,
            feedback_requirement=ai_result.feedback_requirement,
            feedback_security=ai_result.feedback_security,
            feedback_quality=ai_result.feedback_quality,
            feedback_performance=ai_result.feedback_performance,
            critical_issues=ai_result.critical_issues,
            warnings=ai_result.warnings,
            test_suggestions=ai_result.test_suggestions,
        )
        session.add(pr_review)
        await session.flush()
        logger.info("Created new review id=%d for %s#%d", pr_review.id, repo_full_name, pr_number)

    # ── Step 4: Format and post GitHub comment ────────────────────────────
    benchmark = await _compute_benchmark(session, repo.id, ai_result.score_overall)
    comment_body = _format_review_comment(ai_result, pr_number, benchmark)

    comment_id = await github_service.post_review_comment(
        repo_full_name, pr_number, comment_body, installation_id
    )
    if comment_id:
        pr_review.github_comment_id = comment_id

    # ── Step 5: Commit status ─────────────────────────────────────────────
    status_state = "success" if ai_result.score_overall >= 70 else "failure"
    status_desc = (
        f"CodeIntel score: {ai_result.score_overall:.0f}/100 "
        f"({'passed' if status_state == 'success' else 'needs attention'})"
    )
    await github_service.post_status_check(
        repo_full_name, head_sha, status_state, status_desc, installation_id
    )

    # ── Step 6: Slack notification ────────────────────────────────────────
    slack_url = repo.slack_webhook_url or settings.slack_webhook_url
    if slack_url:
        pr_url = f"https://github.com/{repo_full_name}/pull/{pr_number}"
        await slack_service.send_review_notification(
            slack_webhook_url=slack_url,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            pr_title=pr_details["title"],
            pr_author=pr_details["author"],
            score_overall=ai_result.score_overall,
            score_requirement=ai_result.score_requirement,
            score_security=ai_result.score_security,
            score_quality=ai_result.score_quality,
            score_performance=ai_result.score_performance,
            critical_issues=ai_result.critical_issues,
            pr_url=pr_url,
        )

    await session.commit()

    from app.utils.cache import cache_delete, cache_delete_pattern
    await cache_delete(f"codeintel:{repo.id}:stats")
    await cache_delete(f"codeintel:{repo.id}:leaderboard")
    await cache_delete_pattern(f"codeintel:{repo.id}:reviews:*")

    logger.info(
        "Review pipeline complete for %s#%d (overall=%.1f)",
        repo_full_name,
        pr_number,
        ai_result.score_overall,
    )
    return pr_review
