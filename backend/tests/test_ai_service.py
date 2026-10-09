import json
from unittest.mock import patch

import pytest

from app.services.ai_service import _build_prompt, call_llm_with_retry
from app.schemas import AIReviewOutput


VALID_RESPONSE = {
    "score_overall": 75.0,
    "score_requirement": 80.0,
    "score_security": 70.0,
    "score_quality": 75.0,
    "score_performance": 72.0,
    "feedback_requirement": "Good alignment.",
    "feedback_security": "No critical issues.",
    "feedback_quality": "Clean code.",
    "feedback_performance": "Efficient.",
    "critical_issues": [],
    "warnings": ["Minor: unused variable"],
    "test_suggestions": ["Test edge case X"],
}


async def test_valid_json_parsed_correctly():
    with patch(
        "app.services.ai_service._call_llm_sync",
        return_value=json.dumps(VALID_RESPONSE),
    ):
        result = await call_llm_with_retry("test prompt")
    assert isinstance(result, AIReviewOutput)
    assert result.score_overall == 75.0
    assert result.score_security == 70.0


async def test_score_clamped_above_100():
    over = {**VALID_RESPONSE, "score_overall": 150.0}
    with patch(
        "app.services.ai_service._call_llm_sync",
        return_value=json.dumps(over),
    ):
        result = await call_llm_with_retry("test prompt")
    assert result.score_overall == 100.0


async def test_score_clamped_below_0():
    under = {**VALID_RESPONSE, "score_security": -10.0}
    with patch(
        "app.services.ai_service._call_llm_sync",
        return_value=json.dumps(under),
    ):
        result = await call_llm_with_retry("test prompt")
    assert result.score_security == 0.0


async def test_malformed_json_retries_and_raises():
    with patch(
        "app.services.ai_service._call_llm_sync",
        return_value="not valid json at all !!!",
    ) as mock_llm:
        with pytest.raises(RuntimeError, match="AI review failed after"):
            await call_llm_with_retry("test prompt")
    assert mock_llm.call_count == 3  # must exhaust all MAX_RETRIES attempts


async def test_markdown_fence_stripped():
    # Fenced response: ```json\n{...}\n``` — webhooks.py strips fence via split("```")[1]
    fenced = "```json\n" + json.dumps(VALID_RESPONSE) + "\n```"
    with patch(
        "app.services.ai_service._call_llm_sync", return_value=fenced
    ):
        result = await call_llm_with_retry("test prompt")
    assert result.score_overall == 75.0


def test_prompt_includes_custom_weights():
    prompt = _build_prompt(
        diff="diff content",
        pr_title="Test PR",
        pr_body="Test body",
        linked_issue=None,
        repo_language="Python",
        repo_description="Test repo",
        weights={"requirement": 40, "security": 40, "quality": 10, "performance": 10},
    )
    assert "requirement 40%" in prompt
    assert "security 40%" in prompt
    assert "quality 10%" in prompt
    assert "performance 10%" in prompt


def test_prompt_uses_default_weights_when_none():
    prompt = _build_prompt(
        diff="diff",
        pr_title="T",
        pr_body="B",
        linked_issue=None,
        repo_language="Python",
        repo_description="D",
        weights=None,
    )
    assert "requirement 30%" in prompt
    assert "security 30%" in prompt
    assert "quality 20%" in prompt
    assert "performance 20%" in prompt


def test_prompt_includes_linked_issue():
    issue = {"number": 42, "title": "Fix the bug", "body": "Description of issue."}
    prompt = _build_prompt(
        diff="diff",
        pr_title="Fix",
        pr_body="Fixes #42",
        linked_issue=issue,
        repo_language="Python",
        repo_description="Test repo",
        weights=None,
    )
    assert "Issue #42" in prompt
    assert "Fix the bug" in prompt


def test_prompt_no_linked_issue_shows_placeholder():
    prompt = _build_prompt(
        diff="diff",
        pr_title="T",
        pr_body="B",
        linked_issue=None,
        repo_language="Go",
        repo_description="D",
        weights=None,
    )
    assert "No linked issue found." in prompt
