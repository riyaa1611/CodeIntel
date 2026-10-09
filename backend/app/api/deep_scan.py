"""
Feature 2: Deep Scan Analysis endpoints
POST /api/repos/{repo_id}/deep-scan           → trigger Celery task
GET  /api/repos/{repo_id}/deep-scan/latest    → most recent result
GET  /api/repos/{repo_id}/deep-scan/history   → all results (summary)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.middleware.rate_limit import limiter
from app.models import DeepScanResult, Repository, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["deep-scan"])


# ── Response schemas ──────────────────────────────────────────────────────────

class DeepScanResponse(BaseModel):
    id: int
    repo_id: int
    owner: str
    repo_name: str
    overall_score: float
    architecture_score: float
    security_score: float
    duplication_score: float
    documentation_score: float
    test_coverage_score: float
    critical_findings: list[str]
    warnings: list[str]
    positive_observations: list[str]
    architecture_feedback: str
    security_feedback: str
    duplication_feedback: str
    documentation_feedback: str
    test_coverage_feedback: str
    recommended_actions: list[str]
    files_analyzed: int
    created_at: str

    model_config = {"from_attributes": True}


class DeepScanHistoryItem(BaseModel):
    id: int
    overall_score: float
    files_analyzed: int
    created_at: str

    model_config = {"from_attributes": True}


class DeepScanTriggerResponse(BaseModel):
    status: str
    task_id: str
    repo_id: int


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_repo_or_404(repo_id: int, db: AsyncSession) -> Repository:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/repos/{repo_id}/deep-scan",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DeepScanTriggerResponse,
    summary="Trigger a deep scan of the repository codebase",
)
@limiter.limit("3/hour")
async def trigger_deep_scan(
    request: Request,
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enqueues an AI-powered deep scan of the full repository codebase.
    The scan analyzes up to 30 source files for architecture quality, security
    vulnerabilities, code duplication, documentation, and test coverage.
    Poll GET /api/repos/{repo_id}/deep-scan/latest to retrieve results.
    """
    repo = await _get_repo_or_404(repo_id, db)

    from app.workers.tasks import celery_app
    task = celery_app.send_task(
        "tasks.deep_scan_repository",
        args=[repo.owner, repo.name, repo_id],
    )
    logger.info(
        "Deep scan triggered for %s/%s (repo_id=%d, task_id=%s)",
        repo.owner,
        repo.name,
        repo_id,
        task.id,
    )
    return DeepScanTriggerResponse(status="queued", task_id=task.id, repo_id=repo_id)


@router.get(
    "/repos/{repo_id}/deep-scan/latest",
    response_model=DeepScanResponse,
    summary="Get the most recent deep scan result for a repository",
)
async def get_latest_deep_scan(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the most recent DeepScanResult for the given repository, or 404 if none exists."""
    await _get_repo_or_404(repo_id, db)

    result = await db.execute(
        select(DeepScanResult)
        .where(DeepScanResult.repo_id == repo_id)
        .order_by(DeepScanResult.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="No deep scan results found for this repository")

    return DeepScanResponse(
        id=scan.id,
        repo_id=scan.repo_id,
        owner=scan.owner,
        repo_name=scan.repo_name,
        overall_score=scan.overall_score,
        architecture_score=scan.architecture_score,
        security_score=scan.security_score,
        duplication_score=scan.duplication_score,
        documentation_score=scan.documentation_score,
        test_coverage_score=scan.test_coverage_score,
        critical_findings=scan.critical_findings or [],
        warnings=scan.warnings or [],
        positive_observations=scan.positive_observations or [],
        architecture_feedback=scan.architecture_feedback,
        security_feedback=scan.security_feedback,
        duplication_feedback=scan.duplication_feedback,
        documentation_feedback=scan.documentation_feedback,
        test_coverage_feedback=scan.test_coverage_feedback,
        recommended_actions=scan.recommended_actions or [],
        files_analyzed=scan.files_analyzed,
        created_at=scan.created_at.isoformat(),
    )


@router.get(
    "/repos/{repo_id}/deep-scan/history",
    response_model=list[DeepScanHistoryItem],
    summary="Get deep scan history for a repository",
)
async def get_deep_scan_history(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all deep scan results for the given repository, ordered newest first."""
    await _get_repo_or_404(repo_id, db)

    result = await db.execute(
        select(DeepScanResult)
        .where(DeepScanResult.repo_id == repo_id)
        .order_by(DeepScanResult.created_at.desc())
    )
    scans = result.scalars().all()

    return [
        DeepScanHistoryItem(
            id=s.id,
            overall_score=s.overall_score,
            files_analyzed=s.files_analyzed,
            created_at=s.created_at.isoformat(),
        )
        for s in scans
    ]
