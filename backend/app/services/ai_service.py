import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.schemas import AIReviewOutput

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 3


def _build_prompt(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
) -> str:
    issue_section = ""
    if linked_issue:
        issue_section = f"""
## Linked GitHub Issue
**Issue #{linked_issue['number']}: {linked_issue['title']}**
{linked_issue.get('body', 'No description provided.')}
"""
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
Review this Pull Request across exactly 4 dimensions and return ONLY valid JSON with no markdown, no code fences, no explanation — just raw JSON.

Score each dimension from 0 to 100:

1. **Requirement Alignment (score_requirement):** Does the code correctly implement what the linked issue/PR description requires? Are all acceptance criteria met?

2. **Security (score_security):** Are there SQL injection, XSS, SSRF, insecure deserialization, hardcoded secrets, improper input validation, or other OWASP Top 10 vulnerabilities? Is authentication/authorization handled correctly?

3. **Code Quality (score_quality):** Is the code well-structured, readable, and maintainable? Does it follow language idioms and best practices? Are there code smells, duplication, or dead code?

4. **Performance (score_performance):** Are there N+1 queries, missing indexes, synchronous blocking calls, memory leaks, inefficient algorithms, or missing caching opportunities?

For score_overall, compute a weighted average: requirement 30%, security 30%, quality 20%, performance 20%.

Identify critical issues (must fix before merge), warnings (should address), and concrete test case suggestions.

Return ONLY this JSON structure with no additional text:
{{
  "score_overall": <number 0-100>,
  "score_requirement": <number 0-100>,
  "score_security": <number 0-100>,
  "score_quality": <number 0-100>,
  "score_performance": <number 0-100>,
  "feedback_requirement": "<detailed paragraph about requirement alignment>",
  "feedback_security": "<detailed paragraph about security findings>",
  "feedback_quality": "<detailed paragraph about code quality>",
  "feedback_performance": "<detailed paragraph about performance>",
  "critical_issues": ["<issue 1>", "<issue 2>"],
  "warnings": ["<warning 1>", "<warning 2>"],
  "test_suggestions": ["<test case 1>", "<test case 2>", "<test case 3>"]
}}"""


async def call_llm_with_retry(prompt: str) -> AIReviewOutput:
    """Call OpenRouter API with retry logic on malformed JSON."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codeintel-review",
        "X-Title": "CodeIntel PR Review",
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                logger.info(
                    "Calling OpenRouter (model=%s, attempt=%d/%d)",
                    settings.openrouter_model,
                    attempt,
                    MAX_RETRIES,
                )
                response = await client.post(
                    OPENROUTER_API_URL, headers=headers, json=payload
                )
                response.raise_for_status()

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if model disobeyed instructions
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]
                raw_content = raw_content.strip()

            parsed = json.loads(raw_content)
            review = AIReviewOutput(**parsed)
            logger.info(
                "AI review completed successfully (overall score=%.1f)", review.score_overall
            )
            return review

        except json.JSONDecodeError as exc:
            logger.warning(
                "Attempt %d/%d: JSON decode error from LLM: %s", attempt, MAX_RETRIES, exc
            )
            last_error = exc
        except KeyError as exc:
            logger.warning(
                "Attempt %d/%d: Unexpected LLM response structure: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            last_error = exc
        except Exception as exc:
            logger.error(
                "Attempt %d/%d: LLM call failed: %s", attempt, MAX_RETRIES, exc
            )
            last_error = exc
            if attempt == MAX_RETRIES:
                break

    raise RuntimeError(
        f"AI review failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


async def generate_review(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
) -> AIReviewOutput:
    """Build prompt and execute AI review with full retry logic."""
    prompt = _build_prompt(
        diff=diff,
        pr_title=pr_title,
        pr_body=pr_body,
        linked_issue=linked_issue,
        repo_language=repo_language,
        repo_description=repo_description,
    )
    return await call_llm_with_retry(prompt)
