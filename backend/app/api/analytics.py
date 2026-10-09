import hashlib
import json as _json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import PRReview, Repository, ScanSchedule, User
from app.utils.cache import cache_get, cache_delete, cache_delete_pattern, cache_set
from app.schemas import (
    AuthorTrendPoint,
    BenchmarkResult,
    DimensionAverages,
    LeaderboardEntry,
    PaginatedPRReviews,
    PRReviewListItem,
    PRReviewResponse,
    RepoConfigResponse,
    RepoConfigUpdate,
    RepositoryCreate,
    RepositoryResponse,
    RepoStats,
    ScoreDistribution,
    SlackWebhookUpdate,
    ScanScheduleResponse,
    ScanScheduleUpdate,
    TrendDataPoint,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analytics"])


# ── Repository Endpoints ──────────────────────────────────────────────────────

@router.get("/repos", response_model=list[RepositoryResponse])
async def list_repos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all connected repositories."""
    result = await db.execute(select(Repository).order_by(Repository.created_at.desc()))
    repos = result.scalars().all()
    return repos


@router.post(
    "/repos",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repo(
    body: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Register a new repository for CodeIntel reviews."""
    full_name = body.github_repo_full_name.strip()

    existing = await db.execute(
        select(Repository).where(Repository.full_name == full_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository '{full_name}' is already registered",
        )

    parts = full_name.split("/", 1)
    owner, name = parts[0], parts[1] if len(parts) > 1 else full_name

    # Try to fetch GitHub repo ID
    github_repo_id = None
    try:
        from app.services.github_service import get_repo_metadata
        meta = await get_repo_metadata(full_name)
        github_repo_id = meta.get("github_repo_id")
    except Exception as exc:
        logger.warning("Could not fetch GitHub metadata for %s: %s", full_name, exc)

    repo = Repository(
        github_repo_id=github_repo_id,
        full_name=full_name,
        owner=owner,
        name=name,
        slack_webhook_url=body.slack_webhook_url,
    )
    db.add(repo)
    await db.flush()
    logger.info("Registered repository: %s (id=%d)", full_name, repo.id)
    return repo


@router.patch("/repos/{repo_id}/slack", response_model=RepositoryResponse)
async def update_slack_webhook(
    repo_id: int,
    body: SlackWebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update Slack webhook URL for a repository."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.slack_webhook_url = body.slack_webhook_url
    await db.flush()
    return repo


# ── PR Review Endpoints ───────────────────────────────────────────────────────

@router.get("/repos/{repo_id}/reviews", response_model=PaginatedPRReviews)
async def list_reviews(
    repo_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_score: float | None = Query(default=None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated list of PR reviews for a repository."""
    params_hash = hashlib.md5(
        _json.dumps({"page": page, "limit": limit, "min_score": min_score, "max_score": max_score}).encode()
    ).hexdigest()[:8]
    cache_key = f"codeintel:{repo_id}:reviews:{params_hash}"
    cached = await cache_get(cache_key)
    if cached:
        return _json.loads(cached)

    # Verify repo exists
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    query = select(PRReview).where(PRReview.repo_id == repo_id)

    if min_score is not None:
        query = query.where(PRReview.score_overall >= min_score)
    if max_score is not None:
        query = query.where(PRReview.score_overall <= max_score)

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(PRReview.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    reviews = result.scalars().all()

    result_data = PaginatedPRReviews(
        items=[PRReviewListItem.model_validate(r) for r in reviews],
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )
    await cache_set(cache_key, _json.dumps(result_data.model_dump(), default=str), ttl=30)
    return result_data


@router.get("/repos/{repo_id}/reviews/{review_id}", response_model=PRReviewResponse)
async def get_review(
    repo_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single PR review by ID."""
    result = await db.execute(
        select(PRReview).where(
            PRReview.id == review_id, PRReview.repo_id == repo_id
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


# ── Stats / Analytics Endpoints ───────────────────────────────────────────────

@router.get("/repos/{repo_id}/stats", response_model=RepoStats)
async def get_repo_stats(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate statistics for a repository."""
    cache_key = f"codeintel:{repo_id}:stats"
    cached = await cache_get(cache_key)
    if cached:
        return _json.loads(cached)

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    # Total count
    total_result = await db.execute(
        select(func.count()).where(PRReview.repo_id == repo_id)
    )
    total = total_result.scalar() or 0

    if total == 0:
        result_data = RepoStats(
            total_reviews=0,
            dimension_averages=DimensionAverages(
                avg_overall=0,
                avg_requirement=0,
                avg_security=0,
                avg_quality=0,
                avg_performance=0,
            ),
            score_distribution=ScoreDistribution(low=0, medium=0, high=0),
            trend_data=[],
        )
        await cache_set(cache_key, _json.dumps(result_data.model_dump(), default=str), ttl=60)
        return result_data

    # Dimension averages
    avg_result = await db.execute(
        select(
            func.avg(PRReview.score_overall).label("avg_overall"),
            func.avg(PRReview.score_requirement).label("avg_requirement"),
            func.avg(PRReview.score_security).label("avg_security"),
            func.avg(PRReview.score_quality).label("avg_quality"),
            func.avg(PRReview.score_performance).label("avg_performance"),
        ).where(PRReview.repo_id == repo_id)
    )
    avgs = avg_result.one()

    # Score distribution
    low_result = await db.execute(
        select(func.count()).where(
            PRReview.repo_id == repo_id, PRReview.score_overall <= 40
        )
    )
    medium_result = await db.execute(
        select(func.count()).where(
            PRReview.repo_id == repo_id,
            PRReview.score_overall > 40,
            PRReview.score_overall <= 70,
        )
    )
    high_result = await db.execute(
        select(func.count()).where(
            PRReview.repo_id == repo_id, PRReview.score_overall > 70
        )
    )

    # 30-day trend
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
    trend_result = await db.execute(
        select(
            func.date(PRReview.created_at).label("day"),
            func.avg(PRReview.score_overall).label("avg_score"),
            func.count().label("pr_count"),
        )
        .where(PRReview.repo_id == repo_id, PRReview.created_at >= cutoff)
        .group_by(func.date(PRReview.created_at))
        .order_by(func.date(PRReview.created_at))
    )
    trend_rows = trend_result.all()

    trend_data = [
        TrendDataPoint(
            date=str(row.day),
            avg_score=round(float(row.avg_score), 1),
            pr_count=row.pr_count,
        )
        for row in trend_rows
    ]

    result_data = RepoStats(
        total_reviews=total,
        dimension_averages=DimensionAverages(
            avg_overall=round(float(avgs.avg_overall or 0), 1),
            avg_requirement=round(float(avgs.avg_requirement or 0), 1),
            avg_security=round(float(avgs.avg_security or 0), 1),
            avg_quality=round(float(avgs.avg_quality or 0), 1),
            avg_performance=round(float(avgs.avg_performance or 0), 1),
        ),
        score_distribution=ScoreDistribution(
            low=low_result.scalar() or 0,
            medium=medium_result.scalar() or 0,
            high=high_result.scalar() or 0,
        ),
        trend_data=trend_data,
    )
    await cache_set(cache_key, _json.dumps(result_data.model_dump(), default=str), ttl=60)
    return result_data


@router.get("/repos/{repo_id}/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-author leaderboard ranked by average overall score."""
    cache_key = f"codeintel:{repo_id}:leaderboard"
    cached = await cache_get(cache_key)
    if cached:
        return _json.loads(cached)

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(
            PRReview.pr_author.label("author"),
            func.count().label("pr_count"),
            func.avg(PRReview.score_overall).label("avg_overall"),
            func.avg(PRReview.score_security).label("avg_security"),
            func.avg(PRReview.score_quality).label("avg_quality"),
            func.avg(PRReview.score_requirement).label("avg_requirement"),
            func.avg(PRReview.score_performance).label("avg_performance"),
        )
        .where(PRReview.repo_id == repo_id)
        .group_by(PRReview.pr_author)
        .order_by(func.avg(PRReview.score_overall).desc())
    )
    rows = result.all()

    result_data = [
        LeaderboardEntry(
            rank=idx + 1,
            author=row.author,
            pr_count=row.pr_count,
            avg_overall=round(float(row.avg_overall or 0), 1),
            avg_security=round(float(row.avg_security or 0), 1),
            avg_quality=round(float(row.avg_quality or 0), 1),
            avg_requirement=round(float(row.avg_requirement or 0), 1),
            avg_performance=round(float(row.avg_performance or 0), 1),
        )
        for idx, row in enumerate(rows)
    ]
    await cache_set(
        cache_key,
        _json.dumps([e.model_dump() for e in result_data], default=str),
        ttl=300,
    )
    return result_data


@router.get("/repos/{repo_id}/benchmark/{score}", response_model=BenchmarkResult)
async def get_benchmark(
    repo_id: int,
    score: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return what percentile a given score is in this repository."""
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    total_result = await db.execute(
        select(func.count()).where(PRReview.repo_id == repo_id)
    )
    total = total_result.scalar() or 0

    if total == 0:
        return BenchmarkResult(
            score=score,
            percentile=100.0,
            total_reviews=0,
            better_than_count=0,
        )

    better_result = await db.execute(
        select(func.count()).where(
            PRReview.repo_id == repo_id, PRReview.score_overall < score
        )
    )
    better_count = better_result.scalar() or 0
    percentile = round((better_count / total) * 100.0, 1)

    return BenchmarkResult(
        score=score,
        percentile=percentile,
        total_reviews=total,
        better_than_count=better_count,
    )


@router.get("/repos/{repo_id}/reviews/{review_id}/diff")
async def get_review_diff(
    repo_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the unified diff for the PR associated with a review from GitHub."""
    from app.config import settings

    # Load the review + repo in one round-trip
    result = await db.execute(
        select(PRReview, Repository)
        .join(Repository, PRReview.repo_id == Repository.id)
        .where(PRReview.id == review_id, PRReview.repo_id == repo_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")

    review, repo = row

    headers: dict[str, str] = {
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"

    url = f"https://api.github.com/repos/{repo.full_name}/pulls/{review.pr_number}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="PR not found on GitHub")
        resp.raise_for_status()
        return Response(
            content=resp.text,
            media_type="text/plain",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": 'inline; filename="pr.diff"',
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch diff for PR %d: %s", review.pr_number, exc)
        raise HTTPException(status_code=502, detail="Failed to fetch diff from GitHub")


@router.get("/repos/{repo_id}/authors/{author}/trend", response_model=list[AuthorTrendPoint])
async def get_author_trend(
    repo_id: int,
    author: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-PR score trajectory for a specific author (chronological order)."""
    author_hash = hashlib.md5(author.encode()).hexdigest()[:12]
    cache_key = f"codeintel:{repo_id}:author_trend:{author_hash}"
    cached = await cache_get(cache_key)
    if cached:
        return _json.loads(cached)

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(PRReview)
        .where(PRReview.repo_id == repo_id, PRReview.pr_author == author)
        .order_by(PRReview.created_at.asc())
    )
    reviews = result.scalars().all()

    result_data = [
        AuthorTrendPoint(
            date=r.created_at.strftime("%Y-%m-%d"),
            score_overall=round(r.score_overall, 1),
            score_requirement=round(r.score_requirement, 1),
            score_security=round(r.score_security, 1),
            score_quality=round(r.score_quality, 1),
            score_performance=round(r.score_performance, 1),
            pr_number=r.pr_number,
            pr_title=r.pr_title,
        )
        for r in reviews
    ]
    await cache_set(
        cache_key,
        _json.dumps([p.model_dump() for p in result_data], default=str),
        ttl=90,
    )
    return result_data


# ── Repo Config Endpoints ─────────────────────────────────────────────────────

_DEFAULT_WEIGHTS = {"requirement": 30, "security": 30, "quality": 20, "performance": 20}


@router.get("/repos/{repo_id}/config", response_model=RepoConfigResponse)
async def get_repo_config(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the scoring weight and threshold configuration for a repository."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    cfg = repo.repo_config or {}
    weights = cfg.get("weights", _DEFAULT_WEIGHTS)
    return RepoConfigResponse(weights=weights, scan_threshold=cfg.get("scan_threshold"))


@router.patch("/repos/{repo_id}/config", response_model=RepoConfigResponse)
async def update_repo_config(
    repo_id: int,
    body: RepoConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update scoring weight and threshold configuration for a repository (admin only)."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    new_cfg = {**(repo.repo_config or {}), "weights": body.weights.model_dump()}
    if body.scan_threshold is not None:
        new_cfg["scan_threshold"] = body.scan_threshold
    else:
        new_cfg.pop("scan_threshold", None)
    repo.repo_config = new_cfg
    await db.commit()
    return RepoConfigResponse(weights=body.weights, scan_threshold=body.scan_threshold)


# ── Scan Schedule Endpoints ───────────────────────────────────────────────────

_FREQUENCY_DELTA: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}


@router.get(
    "/repos/{repo_id}/scan-schedule",
    response_model=ScanScheduleResponse,
    responses={404: {"description": "No schedule configured"}},
)
async def get_scan_schedule(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the active deep-scan schedule for a repository, if any."""
    result = await db.execute(
        select(ScanSchedule).where(ScanSchedule.repo_id == repo_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="No scan schedule configured")
    return schedule


@router.put(
    "/repos/{repo_id}/scan-schedule",
    response_model=ScanScheduleResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_scan_schedule(
    repo_id: int,
    body: ScanScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create or update the deep-scan schedule for a repository (admin only)."""
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    now = datetime.now(tz=timezone.utc)
    next_run = now + _FREQUENCY_DELTA[body.frequency]

    result = await db.execute(
        select(ScanSchedule).where(ScanSchedule.repo_id == repo_id)
    )
    schedule = result.scalar_one_or_none()

    if schedule:
        if schedule.frequency != body.frequency:
            schedule.next_run_at = next_run
        schedule.frequency = body.frequency
        schedule.enabled = body.enabled
    else:
        schedule = ScanSchedule(
            repo_id=repo_id,
            frequency=body.frequency,
            enabled=body.enabled,
            next_run_at=next_run,
        )
        db.add(schedule)

    await db.commit()
    await db.refresh(schedule)
    return schedule


# ── Scan Approval Endpoint ────────────────────────────────────────────────────

@router.get("/scan-approval/{token}", include_in_schema=False)
async def handle_scan_approval(
    token: str,
    action: str = Query(pattern=r"^(approve|dismiss)$"),
):
    """
    One-time approval link for auto-triggered deep scans.
    Called by clicking the Slack notification link (no auth required — token is the auth).
    """
    from app.utils.cache import get_redis_connection
    import json as _j

    redis = get_redis_connection()
    if redis is None:
        raise HTTPException(status_code=503, detail="Service unavailable")

    key = f"codeintel:scan_approval:{token}"
    raw = await redis.get(key)
    if not raw:
        raise HTTPException(status_code=410, detail="Approval link expired or already used")

    payload = _j.loads(raw)
    await redis.delete(key)

    repo_id: int = payload["repo_id"]
    owner: str = payload["owner"]
    repo_name: str = payload["repo_name"]

    if action == "approve":
        from app.workers.tasks import deep_scan_repository
        deep_scan_repository.delay(owner, repo_name, repo_id)
        logger.info("Scan approval accepted: %s/%s (repo_id=%d)", owner, repo_name, repo_id)
        return {"status": "approved", "message": f"Deep scan queued for {owner}/{repo_name}"}
    else:
        logger.info("Scan approval dismissed: %s/%s", owner, repo_name)
        return {"status": "dismissed", "message": "Deep scan dismissed"}


# ── Export Endpoints ──────────────────────────────────────────────────────────

@router.get("/repos/{repo_id}/export/csv")
async def export_reviews_csv(
    repo_id: int,
    from_date: str | None = Query(default=None, description="ISO date YYYY-MM-DD"),
    to_date: str | None = Query(default=None, description="ISO date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export PR reviews as a CSV file, optionally filtered by date range."""
    import csv
    import io
    import re as _re

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    query = select(PRReview).where(PRReview.repo_id == repo_id)

    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
            query = query.where(PRReview.created_at >= from_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid from_date format, expected YYYY-MM-DD")

    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
            query = query.where(PRReview.created_at < to_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid to_date format, expected YYYY-MM-DD")

    query = query.order_by(PRReview.created_at.desc())
    result = await db.execute(query)
    reviews = result.scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "pr_number", "pr_title", "pr_author", "head_sha",
        "score_overall", "score_requirement", "score_security",
        "score_quality", "score_performance", "created_at",
    ])
    for r in reviews:
        writer.writerow([
            r.id, r.pr_number, r.pr_title, r.pr_author, r.head_sha,
            round(r.score_overall, 2), round(r.score_requirement, 2),
            round(r.score_security, 2), round(r.score_quality, 2),
            round(r.score_performance, 2),
            r.created_at.isoformat(),
        ])

    safe_name = _re.sub(r"[^\w\-.]", "_", repo.name)
    filename = f"{safe_name}_reviews"
    if from_date:
        filename += f"_from_{from_date}"
    if to_date:
        filename += f"_to_{to_date}"
    filename += ".csv"

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/repos/{repo_id}/export/pdf")
async def export_monthly_pdf(
    repo_id: int,
    month: str = Query(..., description="Month in YYYY-MM format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a PDF monthly digest report for a repository."""
    import re

    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(status_code=422, detail="month must be YYYY-MM")

    try:
        year, mon = int(month[:4]), int(month[5:7])
        from_dt = datetime(year, mon, 1, tzinfo=timezone.utc)
        to_dt = datetime(year + (1 if mon == 12 else 0), 1 if mon == 12 else mon + 1, 1, tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid month value")

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    stats_result = await db.execute(
        select(
            func.count().label("total"),
            func.avg(PRReview.score_overall).label("avg_overall"),
            func.avg(PRReview.score_security).label("avg_security"),
            func.avg(PRReview.score_quality).label("avg_quality"),
            func.avg(PRReview.score_requirement).label("avg_req"),
            func.avg(PRReview.score_performance).label("avg_perf"),
        ).where(
            PRReview.repo_id == repo_id,
            PRReview.created_at >= from_dt,
            PRReview.created_at < to_dt,
        )
    )
    stats = stats_result.one()

    reviews_result = await db.execute(
        select(PRReview)
        .where(PRReview.repo_id == repo_id, PRReview.created_at >= from_dt, PRReview.created_at < to_dt)
        .order_by(PRReview.score_overall.asc())
        .limit(50)
    )
    reviews = reviews_result.scalars().all()

    authors_result = await db.execute(
        select(
            PRReview.pr_author.label("author"),
            func.count().label("pr_count"),
            func.avg(PRReview.score_overall).label("avg_score"),
        )
        .where(PRReview.repo_id == repo_id, PRReview.created_at >= from_dt, PRReview.created_at < to_dt)
        .group_by(PRReview.pr_author)
        .order_by(func.avg(PRReview.score_overall).desc())
        .limit(10)
    )
    top_authors = authors_result.all()

    # Build PDF using reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        import io as _io

        buf = _io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        blue = colors.HexColor("#2563eb")
        gray = colors.HexColor("#6b7280")
        light = colors.HexColor("#f3f4f6")

        elements = []

        # Title
        title_style = ParagraphStyle("title", parent=styles["Title"], textColor=blue, fontSize=20)
        elements.append(Paragraph(f"CodeIntel Monthly Report — {month}", title_style))
        elements.append(Paragraph(f"<font color='#6b7280'>Repository: {repo.full_name}</font>", styles["Normal"]))
        elements.append(Spacer(1, 0.5*cm))

        # Summary stats
        if stats.total:
            summary_data = [
                ["Metric", "Value"],
                ["Total PRs Reviewed", str(stats.total)],
                ["Avg Overall Score", f"{float(stats.avg_overall or 0):.1f} / 100"],
                ["Avg Requirement", f"{float(stats.avg_req or 0):.1f}"],
                ["Avg Security", f"{float(stats.avg_security or 0):.1f}"],
                ["Avg Code Quality", f"{float(stats.avg_quality or 0):.1f}"],
                ["Avg Performance", f"{float(stats.avg_perf or 0):.1f}"],
            ]
        else:
            summary_data = [["Metric", "Value"], ["Total PRs Reviewed", "0 (no reviews this month)"]]

        summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), blue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(Paragraph("Summary", styles["Heading2"]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*cm))

        # Top authors
        if top_authors:
            author_data = [["Rank", "Author", "PRs", "Avg Score"]]
            for i, a in enumerate(top_authors):
                author_data.append([
                    f"#{i+1}", f"@{a.author}", str(a.pr_count), f"{float(a.avg_score or 0):.1f}"
                ])
            author_table = Table(author_data, colWidths=[2*cm, 7*cm, 3*cm, 4*cm])
            author_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(Paragraph("Top Authors", styles["Heading2"]))
            elements.append(author_table)
            elements.append(Spacer(1, 0.5*cm))

        # PR list (lowest scores first — needs attention)
        if reviews:
            pr_data = [["PR #", "Author", "Title", "Score"]]
            for r in reviews[:20]:
                title_trunc = r.pr_title[:45] + "…" if len(r.pr_title) > 45 else r.pr_title
                pr_data.append([
                    f"#{r.pr_number}", f"@{r.pr_author}", title_trunc, f"{r.score_overall:.0f}"
                ])
            pr_table = Table(pr_data, colWidths=[2*cm, 4*cm, 9*cm, 2*cm])
            pr_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(Paragraph("PR Reviews (lowest scoring first)", styles["Heading2"]))
            elements.append(pr_table)

        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph(
            f"<font color='#9ca3af' size='8'>Generated by CodeIntel · {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</font>",
            styles["Normal"],
        ))

        doc.build(elements)
        pdf_bytes = buf.getvalue()
        buf.close()

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF generation requires the 'reportlab' package. Install with: pip install reportlab",
        )

    safe_name = re.sub(r"[^\w\-.]", "_", repo.name)
    filename = f"{safe_name}_digest_{month}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
