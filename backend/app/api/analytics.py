import hashlib
import json as _json
import logging
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import PRReview, Repository, User
from app.utils.cache import cache_get, cache_set
from app.schemas import (
    BenchmarkResult,
    DimensionAverages,
    LeaderboardEntry,
    PaginatedPRReviews,
    PRReviewListItem,
    PRReviewResponse,
    RepositoryCreate,
    RepositoryResponse,
    RepoStats,
    ScoreDistribution,
    SlackWebhookUpdate,
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
