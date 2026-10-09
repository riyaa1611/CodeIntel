import json
import logging
from typing import Any

from openai import OpenAI

from app.config import settings
from app.schemas import AIReviewOutput

logger = logging.getLogger(__name__)
MAX_RETRIES = 3

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Keep _client for backwards compat (tasks.py imports it)
_client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url=OPENROUTER_BASE,
)


def _call_llm_with_key_fallback(messages: list[dict], max_tokens: int = 4096) -> str:
    """Try each OpenRouter key in order, rotating on credit/auth errors."""
    keys = settings.openrouter_api_keys
    if not keys:
        raise RuntimeError("No OpenRouter API keys configured")

    last_err: Exception | None = None
    for i, key in enumerate(keys):
        client = OpenAI(api_key=key, base_url=OPENROUTER_BASE)
        try:
            response = client.chat.completions.create(
                model=settings.openrouter_model,
                max_tokens=max_tokens,
                messages=messages,
            )
            if i > 0:
                logger.info("Key fallback succeeded on key #%d", i + 1)
            return response.choices[0].message.content.strip()
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status in (401, 402, 429):
                logger.warning("Key #%d exhausted/unauthorized (status=%s), trying next", i + 1, status)
                last_err = exc
                continue
            raise

    raise RuntimeError(f"All {len(keys)} OpenRouter keys failed. Last error: {last_err}")


def _build_prompt(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
    weights: dict[str, int] | None = None,
) -> str:
    w = weights or {"requirement": 30, "security": 30, "quality": 20, "performance": 20}
    if linked_issue:
        issue_section = (
            f"\n## Linked GitHub Issue\n"
            f"**Issue #{linked_issue['number']}: {linked_issue['title']}**\n"
            f"{linked_issue.get('body', 'No description provided.')}\n"
        )
    else:
        issue_section = "\n## Linked GitHub Issue\nNo linked issue found.\n"

    return f"""You are CodeIntel, an expert AI code reviewer. Analyze the provided Pull Request and return a structured JSON review.

## Repository
- **Language:** {repo_language}
- **Description:** {repo_description or 'Not provided'}

## Pull Request
**Title:** {pr_title}

**Description:**
{pr_body or 'No description provided.'}
{issue_section}
## Code Diff
```diff
{diff}
```

## Your Task
Review this Pull Request across exactly 4 dimensions and return ONLY valid JSON — no markdown, no code fences, no explanation.

Score each dimension from 0 to 100:
1. **Requirement Alignment (score_requirement):** Does the code implement what the issue/PR description requires?
2. **Security (score_security):** OWASP Top 10, hardcoded secrets, auth/authz issues.
3. **Code Quality (score_quality):** Structure, readability, idioms, code smells.
4. **Performance (score_performance):** N+1 queries, blocking calls, missing indexes.

For score_overall, use weighted average: requirement {w['requirement']}%, security {w['security']}%, quality {w['quality']}%, performance {w['performance']}%.

Return ONLY this JSON:
{{
  "score_overall": <number 0-100>,
  "score_requirement": <number 0-100>,
  "score_security": <number 0-100>,
  "score_quality": <number 0-100>,
  "score_performance": <number 0-100>,
  "feedback_requirement": "<detailed paragraph>",
  "feedback_security": "<detailed paragraph>",
  "feedback_quality": "<detailed paragraph>",
  "feedback_performance": "<detailed paragraph>",
  "critical_issues": ["<issue>", ...],
  "warnings": ["<warning>", ...],
  "test_suggestions": ["<test case>", ...]
}}"""


def _call_llm_sync(prompt: str) -> str:
    """Synchronous OpenRouter call with key fallback — safe to run in executor."""
    return _call_llm_with_key_fallback([{"role": "user", "content": prompt}])


async def call_llm_with_retry(prompt: str) -> AIReviewOutput:
    """Call OpenRouter API with retry logic on malformed JSON."""
    import asyncio

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Calling OpenRouter (model=%s, attempt=%d/%d)",
                settings.openrouter_model, attempt, MAX_RETRIES,
            )
            loop = asyncio.get_running_loop()
            raw = await loop.run_in_executor(None, _call_llm_sync, prompt)

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)
            review = AIReviewOutput(**parsed)
            logger.info("AI review completed (overall=%.1f)", review.score_overall)
            return review

        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Attempt %d/%d: parse error: %s", attempt, MAX_RETRIES, exc)
            last_error = exc
        except Exception as exc:
            logger.error("Attempt %d/%d: LLM error: %s", attempt, MAX_RETRIES, exc)
            last_error = exc
            if attempt == MAX_RETRIES:
                break

    raise RuntimeError(
        f"AI review failed after {MAX_RETRIES} attempts. Last: {last_error}"
    )


async def generate_review(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
    weights: dict[str, int] | None = None,
) -> AIReviewOutput:
    """Build prompt and execute AI review."""
    prompt = _build_prompt(
        diff=diff,
        pr_title=pr_title,
        pr_body=pr_body,
        linked_issue=linked_issue,
        repo_language=repo_language,
        repo_description=repo_description,
        weights=weights,
    )
    return await call_llm_with_retry(prompt)
