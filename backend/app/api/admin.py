import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.config import settings
from app.database import get_db
from app.models import TaskFailure

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_token(x_admin_token: str = Header(default="")):
    """Basic static-token guard. Will be replaced by GitHub OAuth in Phase 3."""
    if settings.app_env != "development" and x_admin_token != settings.session_secret:
        raise HTTPException(status_code=403, detail="Invalid admin token")


@router.get("/failures")
async def list_failures(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """List the 100 most recent failed Celery tasks."""
    result = await db.execute(
        select(TaskFailure).order_by(desc(TaskFailure.failed_at)).limit(100)
    )
    failures = result.scalars().all()
    return [
        {
            "id": f.id,
            "task_name": f.task_name,
            "task_args": f.task_args,
            "error_message": f.error_message,
            "traceback_text": f.traceback_text,
            "failed_at": f.failed_at.isoformat(),
            "retry_count": f.retry_count,
        }
        for f in failures
    ]


@router.post("/failures/{failure_id}/retry")
async def retry_failure(
    failure_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """Re-enqueue a failed task with its original arguments."""
    result = await db.execute(select(TaskFailure).where(TaskFailure.id == failure_id))
    failure = result.scalar_one_or_none()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure not found")

    from app.workers.tasks import celery_app

    allowed_tasks = {
        "tasks.process_pr_review",
        "tasks.deep_scan_repository",
    }
    if failure.task_name not in allowed_tasks:
        raise HTTPException(status_code=400, detail=f"Cannot retry task: {failure.task_name}")

    args = failure.task_args.get("args", [])
    kwargs = failure.task_args.get("kwargs", {})
    celery_app.send_task(failure.task_name, args=args, kwargs=kwargs)

    failure.retry_count += 1
    await db.commit()
    return {"status": "queued", "task_name": failure.task_name}
