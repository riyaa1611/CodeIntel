import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import jwt

from app.config import settings

logger = logging.getLogger(__name__)

_ISSUE_REF_PATTERN = re.compile(
    r"(?:closes?|fixes?|resolves?)\s+#(\d+)", re.IGNORECASE
)

# Cache: installation_id -> (token, expires_at_unix_timestamp)
_token_cache: dict[int, tuple[str, float]] = {}


def _generate_app_jwt() -> str:
    """Generate a GitHub App JWT signed with the private key, valid for 10 minutes."""
    if settings.github_private_key:
        private_key = settings.github_private_key.replace("\\n", "\n")
    else:
        private_key = Path(settings.github_private_key_path).read_text()
    now = int(time.time())
    payload = {
        "iat": now - 60,   # issued 60s ago to handle clock drift
        "exp": now + 600,  # valid for 10 minutes
        "iss": settings.github_app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    """Return an installation access token, refreshing from GitHub if near expiry."""
    cached = _token_cache.get(installation_id)
    if cached:
        token, expires_at = cached
        if time.time() < expires_at - 60:  # refresh 60s before expiry
            return token

    app_jwt = _generate_app_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github.v3+json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    token = data["token"]
    expires_at = datetime.fromisoformat(
        data["expires_at"].replace("Z", "+00:00")
    ).timestamp()
    _token_cache[installation_id] = (token, expires_at)
    logger.debug("Fetched new installation token for installation %d", installation_id)
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


async def get_pr_diff(repo_full_name: str, pr_number: int, installation_id: int) -> str:
    """Fetch the raw unified diff for a pull request."""
    token = await get_installation_token(installation_id)
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
    }
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            diff = response.text
            # Truncate to 50k chars to stay within LLM context limits
            if len(diff) > 50_000:
                diff = diff[:50_000] + "\n\n[DIFF TRUNCATED — too large]"
            return diff
    except httpx.HTTPStatusError as exc:
        logger.error("Failed to fetch PR diff for %s#%d: %s", repo_full_name, pr_number, exc)
        raise


async def get_pr_details(
    repo_full_name: str, pr_number: int, installation_id: int
) -> dict[str, Any]:
    """Return title, body, author, labels, head_sha for a PR."""
    token = await get_installation_token(installation_id)
    headers = _auth_headers(token)
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "title": data.get("title", ""),
                "body": data.get("body") or "",
                "author": data.get("user", {}).get("login", "unknown"),
                "labels": [lbl["name"] for lbl in data.get("labels", [])],
                "head_sha": data.get("head", {}).get("sha", ""),
                "base_branch": data.get("base", {}).get("ref", ""),
                "draft": data.get("draft", False),
            }
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Failed to fetch PR details for %s#%d: %s", repo_full_name, pr_number, exc
        )
        raise


async def get_linked_issue(
    repo_full_name: str, pr_body: str, installation_id: int
) -> dict[str, Any] | None:
    """Extract a linked issue number from the PR body and fetch its details."""
    match = _ISSUE_REF_PATTERN.search(pr_body)
    if not match:
        return None

    issue_number = int(match.group(1))
    token = await get_installation_token(installation_id)
    headers = _auth_headers(token)
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "number": issue_number,
                "title": data.get("title", ""),
                "body": data.get("body") or "",
                "labels": [lbl["name"] for lbl in data.get("labels", [])],
                "state": data.get("state", ""),
            }
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Could not fetch linked issue #%d for %s: %s",
            issue_number,
            repo_full_name,
            exc,
        )
        return None


async def get_repo_metadata(
    repo_full_name: str, installation_id: int
) -> dict[str, Any]:
    """Return primary language and description for a repository."""
    token = await get_installation_token(installation_id)
    headers = _auth_headers(token)
    url = f"https://api.github.com/repos/{repo_full_name}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "language": data.get("language") or "Unknown",
                "description": data.get("description") or "",
                "default_branch": data.get("default_branch", "main"),
                "github_repo_id": data.get("id"),
            }
    except httpx.HTTPStatusError as exc:
        logger.error("Failed to fetch repo metadata for %s: %s", repo_full_name, exc)
        return {"language": "Unknown", "description": "", "default_branch": "main", "github_repo_id": None}


async def post_review_comment(
    repo_full_name: str, pr_number: int, comment_body: str, installation_id: int
) -> int | None:
    """Post an issue comment on a PR and return the comment ID."""
    token = await get_installation_token(installation_id)
    headers = _auth_headers(token)
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, headers=headers, json={"body": comment_body}
            )
            response.raise_for_status()
            data = response.json()
            comment_id = data.get("id")
            logger.info(
                "Posted review comment #%s on %s#%d", comment_id, repo_full_name, pr_number
            )
            return comment_id
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Failed to post review comment on %s#%d: %s", repo_full_name, pr_number, exc
        )
        return None


async def post_status_check(
    repo_full_name: str,
    head_sha: str,
    state: str,
    description: str,
    installation_id: int,
) -> bool:
    """Set a GitHub commit status check. state must be: success, failure, error, pending."""
    token = await get_installation_token(installation_id)
    headers = _auth_headers(token)
    url = f"https://api.github.com/repos/{repo_full_name}/statuses/{head_sha}"
    payload = {
        "state": state,
        "description": description[:140],  # GitHub limit
        "context": "CodeIntel / AI Review",
        "target_url": "",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(
                "Set commit status '%s' on %s @ %s", state, repo_full_name, head_sha[:8]
            )
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Failed to set commit status on %s @ %s: %s", repo_full_name, head_sha[:8], exc
        )
        return False


async def get_or_create_repo_id(repo_full_name: str, installation_id: int) -> int | None:
    """Fetch the GitHub numeric repo ID."""
    meta = await get_repo_metadata(repo_full_name, installation_id)
    return meta.get("github_repo_id")
