import asyncio
import logging

from celery import Task

from app.config import settings

logger = logging.getLogger(__name__)


def make_celery():
    from celery import Celery

    app = Celery(
        "codeintel",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_time_limit=120,
        task_soft_time_limit=100,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )
    return app


celery_app = make_celery()


@celery_app.task(
    bind=True,
    name="tasks.process_pr_review",
    max_retries=2,
    default_retry_delay=30,
    time_limit=120,
    soft_time_limit=100,
)
def process_pr_review(
    self: Task,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    action: str,
    installation_id: int = 0,
) -> dict:
    """
    Celery task: run the full AI review pipeline for a PR.
    Executes async code by running it in a new event loop.
    """
    logger.info(
        "Task process_pr_review started: %s#%d (sha=%s, action=%s)",
        repo_full_name,
        pr_number,
        head_sha[:8],
        action,
    )

    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.review_service import run_pr_review

        async with AsyncSessionLocal() as session:
            review = await run_pr_review(
                session=session,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                head_sha=head_sha,
                installation_id=installation_id,
            )
            return {
                "review_id": review.id,
                "repo_full_name": repo_full_name,
                "pr_number": pr_number,
                "score_overall": review.score_overall,
            }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run())
        finally:
            loop.close()

        logger.info(
            "Task process_pr_review completed: %s#%d → score=%.1f",
            repo_full_name,
            pr_number,
            result["score_overall"],
        )
        return result

    except Exception as exc:
        logger.error(
            "Task process_pr_review failed for %s#%d: %s",
            repo_full_name,
            pr_number,
            exc,
            exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                "Max retries exceeded for %s#%d — giving up", repo_full_name, pr_number
            )
            return {
                "error": str(exc),
                "repo_full_name": repo_full_name,
                "pr_number": pr_number,
            }
