import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _score_emoji(score: float) -> str:
    if score >= 80:
        return ":white_check_mark:"
    elif score >= 60:
        return ":warning:"
    return ":x:"


async def send_review_notification(
    slack_webhook_url: str,
    repo_full_name: str,
    pr_number: int,
    pr_title: str,
    pr_author: str,
    score_overall: float,
    score_requirement: float,
    score_security: float,
    score_quality: float,
    score_performance: float,
    critical_issues: list[str],
    pr_url: str = "",
) -> bool:
    """Send a structured Slack notification for a completed PR review."""
    if not slack_webhook_url:
        logger.debug("No Slack webhook URL configured, skipping notification")
        return False

    emoji = _score_emoji(score_overall)
    critical_text = (
        "\n".join(f"• {issue}" for issue in critical_issues[:3])
        if critical_issues
        else "_No critical issues_"
    )

    pr_link = f"<{pr_url}|#{pr_number}: {pr_title}>" if pr_url else f"#{pr_number}: {pr_title}"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"CodeIntel Review: {repo_full_name}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*PR {pr_link}*\nAuthor: @{pr_author}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Overall Score*\n{emoji} *{score_overall:.0f}/100*",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Requirement*\n{_score_emoji(score_requirement)} {score_requirement:.0f}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Security*\n{_score_emoji(score_security)} {score_security:.0f}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality*\n{_score_emoji(score_quality)} {score_quality:.0f}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Performance*\n{_score_emoji(score_performance)} {score_performance:.0f}/100",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":rotating_light: *Critical Issues*\n{critical_text}",
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "CodeIntel AI Review • Re-trigger by commenting `/codeintel review` on the PR",
                    }
                ],
            },
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(slack_webhook_url, json=payload)
            response.raise_for_status()
            logger.info(
                "Slack notification sent for %s#%d (score=%.1f)",
                repo_full_name,
                pr_number,
                score_overall,
            )
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Slack notification failed for %s#%d: HTTP %s — %s",
            repo_full_name,
            pr_number,
            exc.response.status_code,
            exc.response.text,
        )
        return False
    except Exception as exc:
        logger.error(
            "Slack notification failed for %s#%d: %s", repo_full_name, pr_number, exc
        )
        return False
