import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest


def _make_sig(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# Minimal valid PR payload matching the fields webhooks.py reads:
#   payload["action"], payload["pull_request"]["draft"], payload["pull_request"]["number"],
#   payload["pull_request"]["head"]["sha"], payload["repository"]["full_name"],
#   payload["installation"]["id"]
VALID_PR_PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "draft": False,
        "number": 1,
        "title": "Test PR",
        "body": "",
        "user": {"login": "dev"},
        "head": {"sha": "abc123"},
        "base": {"ref": "main"},
    },
    "repository": {"full_name": "owner/repo", "id": 1},
    "installation": {"id": 1},
}

# Fake Celery AsyncResult returned by .delay()
_FAKE_TASK = MagicMock()
_FAKE_TASK.id = "fake-task-id-1234"


async def test_valid_signature_returns_202(client):
    body = json.dumps(VALID_PR_PAYLOAD).encode()
    sig = _make_sig(body, "test-webhook-secret")
    with patch("app.workers.tasks.process_pr_review.delay", return_value=_FAKE_TASK):
        resp = await client.post(
            "/webhook/github",
            content=body,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json",
            },
        )
    assert resp.status_code == 202


async def test_invalid_signature_returns_403(client):
    body = json.dumps(VALID_PR_PAYLOAD).encode()
    resp = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=invalidsignature",
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 403


async def test_missing_signature_returns_403(client):
    body = json.dumps(VALID_PR_PAYLOAD).encode()
    resp = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 403


async def test_draft_pr_skipped(client):
    # Draft PRs with action="opened" are accepted (202) but not queued —
    # webhooks.py returns {"status": "ignored", "message": "Draft PR skipped"}
    payload = {
        **VALID_PR_PAYLOAD,
        "pull_request": {**VALID_PR_PAYLOAD["pull_request"], "draft": True},
    }
    body = json.dumps(payload).encode()
    sig = _make_sig(body, "test-webhook-secret")
    resp = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    # Draft PRs are accepted (202 ignored) — not rejected with 4xx
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ignored"


async def test_non_trigger_action_ignored(client):
    # Actions not in {"opened", "synchronize", "reopened"} are ignored with 202
    payload = {**VALID_PR_PAYLOAD, "action": "closed"}
    body = json.dumps(payload).encode()
    sig = _make_sig(body, "test-webhook-secret")
    resp = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ignored"


async def test_unknown_event_type_ignored(client):
    # Event types other than "pull_request" and "issue_comment" are ignored
    body = json.dumps({"action": "created"}).encode()
    sig = _make_sig(body, "test-webhook-secret")
    resp = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ignored"
