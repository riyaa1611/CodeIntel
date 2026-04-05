"""
Feature 3: Smart Repository Preview
GET /api/repos/{repo_id}/preview
"""
import base64
import json
import logging
import re
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Repository, User
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["preview"])

GITHUB_API = "https://api.github.com"

# Deployment/hosting domain patterns
_DEPLOYMENT_DOMAINS = (
    "vercel.app",
    "netlify.app",
    "github.io",
    "herokuapp.com",
    "railway.app",
    "render.com",
    "fly.dev",
)

# Keywords that suggest a URL is a live deployment
_DEPLOYMENT_KEYWORDS = re.compile(
    r"\b(demo|live|deployed|preview|app|site)\b", re.IGNORECASE
)

_URL_PATTERN = re.compile(r'https?://[^\s\)\]"\'<>]+')


def _gh_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    return headers


def _extract_live_urls(markdown: str) -> list[str]:
    """
    Extract URLs from README that appear to be live deployment/demo links.
    Criteria: URL matches a known hosting domain, OR the surrounding line
    contains demo/live/deployed/preview/app/site keywords.
    """
    live_urls: list[str] = []
    seen: set[str] = set()

    for line in markdown.splitlines():
        urls_in_line = _URL_PATTERN.findall(line)
        if not urls_in_line:
            continue
        line_has_keyword = bool(_DEPLOYMENT_KEYWORDS.search(line))
        for url in urls_in_line:
            url = url.rstrip(".,;)")  # strip trailing punctuation
            if url in seen:
                continue
            is_deployment_domain = any(domain in url for domain in _DEPLOYMENT_DOMAINS)
            if is_deployment_domain or line_has_keyword:
                live_urls.append(url)
                seen.add(url)

    return live_urls


@router.get(
    "/repos/{repo_id}/preview",
    summary="Fetch README and live deployment URLs for a connected repository",
)
async def get_repo_preview(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Returns the raw README markdown content and any detected live deployment URLs
    for the given connected repository. Results are cached for 600 seconds.
    """
    cache_key = f"codeintel:preview:{repo_id}"

    cached = await cache_get(cache_key)
    if cached:
        return JSONResponse(content=json.loads(cached))

    # ── Fetch repo from DB ────────────────────────────────────────────────────
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    headers = _gh_headers()
    owner, name = repo.owner, repo.name

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Try /readme endpoint first (handles README.md, readme.md, etc.)
            readme_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{name}/readme", headers=headers
            )

            readme_markdown = ""
            last_updated = ""

            if readme_resp.status_code == 200:
                readme_data: dict[str, Any] = readme_resp.json()
                encoded = readme_data.get("content", "")
                if encoded:
                    try:
                        # GitHub returns base64 with newlines
                        readme_markdown = base64.b64decode(
                            encoded.replace("\n", "")
                        ).decode("utf-8", errors="replace")
                    except Exception as exc:
                        logger.warning("Failed to decode README for %s: %s", repo.full_name, exc)

            # Last pushed date from repo metadata
            repo_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{name}", headers=headers
            )
            if repo_resp.status_code == 200:
                last_updated = repo_resp.json().get("pushed_at", "")

    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error fetching preview for %s: %s", repo.full_name, exc)
        raise HTTPException(status_code=502, detail="GitHub API error")
    except Exception as exc:
        logger.error("Error fetching preview for %s: %s", repo.full_name, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch repository preview")

    live_urls = _extract_live_urls(readme_markdown)

    payload = {
        "readme_markdown": readme_markdown,
        "live_urls": live_urls,
        "last_updated": last_updated,
    }

    await cache_set(cache_key, json.dumps(payload), ttl=600)
    return JSONResponse(content=payload)
