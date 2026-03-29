import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

PR_TRIGGER_ACTIONS = {"opened", "synchronize", "reopened"}


def _verify_signature(body: bytes, signature_header: str | None) -> bool:
    """Verify HMAC SHA-256 signature from GitHub."""
    if not settings.github_webhook_secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not set — skipping signature verification")
        return True

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("Invalid signature format: %s", signature_header[:20])
        return False

    expected_sig = (
        "sha256="
        + hmac.new(
            key=settings.github_webhook_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(expected_sig, signature_header)


@router.post(
    "/github",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=WebhookResponse,
    summary="GitHub webhook receiver",
)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> JSONResponse:
    """
    Receive and process GitHub webhook events.
    Verifies HMAC signature, dispatches PR review tasks asynchronously.
    """
    body = await request.body()

    # ── Signature verification ────────────────────────────────────────────
    if not _verify_signature(body, x_hub_signature_256):
        logger.warning(
            "Invalid webhook signature from delivery %s", x_github_delivery
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    # ── Parse payload ─────────────────────────────────────────────────────
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = x_github_event or "unknown"
    logger.info(
        "Received GitHub event: %s (delivery=%s)", event_type, x_github_delivery
    )

    # ── Handle pull_request events ────────────────────────────────────────
    if event_type == "pull_request":
        action = payload.get("action", "")

        if action not in PR_TRIGGER_ACTIONS:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "ignored", "message": f"Action '{action}' not processed"},
            )

        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        repo_full_name = repo.get("full_name", "")
        pr_number = pr.get("number", 0)
        head_sha = pr.get("head", {}).get("sha", "")
        installation_id = payload.get("installation", {}).get("id", 0)

        if not repo_full_name or not pr_number or not head_sha:
            logger.error("Incomplete PR webhook payload: %s", payload)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields in PR payload",
            )

        # Draft PRs: skip review unless explicitly reopened
        if pr.get("draft", False) and action != "reopened":
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "ignored", "message": "Draft PR skipped"},
            )

        # Dispatch Celery task asynchronously
        from app.workers.tasks import process_pr_review

        task = process_pr_review.delay(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            head_sha=head_sha,
            action=action,
            installation_id=installation_id,
        )

        logger.info(
            "Dispatched review task %s for %s#%d (action=%s, sha=%s)",
            task.id,
            repo_full_name,
            pr_number,
            action,
            head_sha[:8],
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "accepted",
                "message": f"Review task queued for PR #{pr_number}",
                "task_id": task.id,
            },
        )

    # ── Handle issue_comment for /codeintel review re-trigger ─────────────
    elif event_type == "issue_comment":
        action = payload.get("action", "")

        if action != "created":
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "ignored", "message": "Comment action not 'created'"},
            )

        comment_body = payload.get("comment", {}).get("body", "").strip()

        if "/codeintel review" not in comment_body.lower():
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "ignored", "message": "Not a CodeIntel command"},
            )

        # Only works on PR comments, not plain issue comments
        issue = payload.get("issue", {})
        if "pull_request" not in issue:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "ignored", "message": "Command only works on PRs"},
            )

        repo = payload.get("repository", {})
        repo_full_name = repo.get("full_name", "")
        pr_number = issue.get("number", 0)
        installation_id = payload.get("installation", {}).get("id", 0)

        # Fetch current head SHA for this PR
        try:
            from app.services.github_service import get_pr_details

            pr_details = await get_pr_details(repo_full_name, pr_number, installation_id)
            head_sha = pr_details["head_sha"]
        except Exception as exc:
            logger.error(
                "Could not fetch PR details for re-review of %s#%d: %s",
                repo_full_name,
                pr_number,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch PR details for re-review",
            )

        from app.workers.tasks import process_pr_review

        task = process_pr_review.delay(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            head_sha=head_sha,
            action="re-review",
            installation_id=installation_id,
        )

        logger.info(
            "Re-review task %s queued for %s#%d via /codeintel review comment",
            task.id,
            repo_full_name,
            pr_number,
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "accepted",
                "message": f"Re-review task queued for PR #{pr_number}",
                "task_id": task.id,
            },
        )

    # ── Ignore all other event types ──────────────────────────────────────
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "ignored", "message": f"Event type '{event_type}' not handled"},
    )
