"""
Feature 1: Instant Public Repository Analytics
GET /api/public/repo/{owner}/{repo}
"""
import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.middleware.rate_limit import limiter
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])

GITHUB_API = "https://api.github.com"


def _gh_headers() -> dict[str, str]:
    """Return GitHub API headers using personal access token."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    return headers


def _compute_health_score(
    stars: int,
    commits_last_30: int,
    open_issues: int,
    forks: int,
    has_description: bool,
    has_license: bool,
    has_homepage: bool,
) -> float:
    """Compute a repository health score (0-100) from several signals."""
    # Stars (20%): log scale, 10k stars ≈ 100
    stars_score = min(100.0, math.log10(max(stars, 1) + 1) * 40)

    # Recent commit activity (30%): 30+ commits/month = 100
    commits_score = min(100.0, commits_last_30 * 100.0 / 30) if commits_last_30 > 0 else 0.0

    # Issues ratio vs forks (20%): lower is better
    issues_ratio = open_issues / max(forks + 1, 1)
    issues_score = max(0.0, 100.0 - issues_ratio * 10.0)

    # Binary signals (10% each)
    description_score = 100.0 if has_description else 0.0
    license_score = 100.0 if has_license else 0.0
    homepage_score = 100.0 if has_homepage else 0.0

    return round(
        stars_score * 0.20
        + commits_score * 0.30
        + issues_score * 0.20
        + description_score * 0.10
        + license_score * 0.10
        + homepage_score * 0.10,
        1,
    )


@router.get("/repo/{owner}/{repo}", summary="Fetch analytics for any public GitHub repository")
@limiter.limit("20/minute")
async def get_public_repo(request: Request, owner: str, repo: str) -> JSONResponse:
    """
    Returns detailed analytics for any public GitHub repository including star/fork counts,
    language breakdown, contributor list, commit activity, and a computed health score.
    Results are cached for 300 seconds.
    """
    cache_key = f"codeintel:public:{owner}:{repo}"

    cached = await cache_get(cache_key)
    if cached:
        return JSONResponse(content=json.loads(cached))

    headers = _gh_headers()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # ── Repo metadata ──────────────────────────────────────────────────
            repo_resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers)
            if repo_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository not found")
            if repo_resp.status_code in (403, 429):
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded")
            repo_resp.raise_for_status()
            repo_data: dict[str, Any] = repo_resp.json()

            # ── Language breakdown ─────────────────────────────────────────────
            lang_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=headers
            )
            languages: dict[str, int] = lang_resp.json() if lang_resp.status_code == 200 else {}

            # ── Top 10 contributors ────────────────────────────────────────────
            contrib_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contributors?per_page=10&anon=false",
                headers=headers,
            )
            raw_contributors = (
                contrib_resp.json()
                if contrib_resp.status_code == 200 and isinstance(contrib_resp.json(), list)
                else []
            )

            # ── Commit activity (last ~30 days via weekly stats) ───────────────
            activity_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/stats/commit_activity", headers=headers
            )
            commits_last_30 = 0
            if activity_resp.status_code == 200:
                activity = activity_resp.json()
                if isinstance(activity, list) and len(activity) >= 4:
                    commits_last_30 = sum(w.get("total", 0) for w in activity[-4:])

    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error fetching %s/%s: %s", owner, repo, exc)
        raise HTTPException(status_code=502, detail="GitHub API error")
    except Exception as exc:
        logger.error("Unexpected error fetching public repo %s/%s: %s", owner, repo, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch repository data")

    # ── Language percentages ───────────────────────────────────────────────────
    total_bytes = sum(languages.values())
    language_percentages: dict[str, float] = (
        {lang: round(b / total_bytes * 100, 1) for lang, b in languages.items()}
        if total_bytes > 0
        else {}
    )

    # ── Health score ───────────────────────────────────────────────────────────
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    open_issues = repo_data.get("open_issues_count", 0)

    health_score = _compute_health_score(
        stars=stars,
        commits_last_30=commits_last_30,
        open_issues=open_issues,
        forks=forks,
        has_description=bool(repo_data.get("description")),
        has_license=bool(repo_data.get("license")),
        has_homepage=bool(repo_data.get("homepage")),
    )

    # ── Build response payload ─────────────────────────────────────────────────
    result = {
        "full_name": repo_data.get("full_name", f"{owner}/{repo}"),
        "description": repo_data.get("description"),
        "homepage": repo_data.get("homepage") or None,
        "topics": repo_data.get("topics", []),
        "stars": stars,
        "forks": forks,
        "open_issues": open_issues,
        "watchers": repo_data.get("watchers_count", 0),
        "language": repo_data.get("language"),
        "languages": languages,
        "language_percentages": language_percentages,
        "created_at": repo_data.get("created_at", ""),
        "pushed_at": repo_data.get("pushed_at", ""),
        "license": (
            repo_data["license"].get("name") if repo_data.get("license") else None
        ),
        "default_branch": repo_data.get("default_branch", "main"),
        "contributors": [
            {
                "login": c.get("login", ""),
                "contributions": c.get("contributions", 0),
                "avatar_url": c.get("avatar_url", ""),
            }
            for c in raw_contributors[:10]
            if isinstance(c, dict)
        ],
        "commits_last_30_days": commits_last_30,
        "health_score": health_score,
    }

    await cache_set(cache_key, json.dumps(result), ttl=300)
    return JSONResponse(content=result)
