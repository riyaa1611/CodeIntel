import pytest
from sqlalchemy import func, select

from app.models import PRReview, Repository


def _make_review(
    repo_id: int, sha: str, pr_number: int = 1, score: float = 70.0
) -> PRReview:
    return PRReview(
        repo_id=repo_id,
        pr_number=pr_number,
        pr_title=f"PR {pr_number}",
        pr_author="dev",
        head_sha=sha,
        score_overall=score,
        score_requirement=score,
        score_security=score,
        score_quality=score,
        score_performance=score,
    )


async def test_same_sha_only_one_row_exists(db):
    repo = Repository(
        full_name="owner/idempotent-repo", owner="owner", name="idempotent-repo"
    )
    db.add(repo)
    await db.flush()

    review = _make_review(repo.id, "abc123")
    db.add(review)
    await db.commit()

    # Simulate re-reviewing same SHA: update existing row rather than insert a new one
    result = await db.execute(
        select(PRReview).where(
            PRReview.repo_id == repo.id, PRReview.head_sha == "abc123"
        )
    )
    existing = result.scalar_one_or_none()
    assert existing is not None
    existing.score_overall = 85.0
    await db.commit()

    result2 = await db.execute(
        select(PRReview).where(
            PRReview.repo_id == repo.id, PRReview.head_sha == "abc123"
        )
    )
    rows = result2.scalars().all()
    assert len(rows) == 1
    assert rows[0].score_overall == 85.0


async def test_different_sha_creates_new_row(db):
    repo = Repository(
        full_name="owner/multi-sha-repo", owner="owner", name="multi-sha-repo"
    )
    db.add(repo)
    await db.flush()

    db.add(_make_review(repo.id, "sha-v1", score=60.0))
    db.add(_make_review(repo.id, "sha-v2", score=80.0))
    await db.commit()

    result = await db.execute(
        select(PRReview).where(PRReview.repo_id == repo.id)
    )
    rows = result.scalars().all()
    assert len(rows) == 2


async def test_benchmark_percentile_calculation(db):
    repo = Repository(
        full_name="owner/bench-repo", owner="owner", name="bench-repo"
    )
    db.add(repo)
    await db.flush()

    for i, score in enumerate([20.0, 40.0, 60.0, 80.0, 100.0]):
        db.add(_make_review(repo.id, f"sha{i}", pr_number=i + 1, score=score))
    await db.commit()

    total = await db.scalar(
        select(func.count()).where(PRReview.repo_id == repo.id)
    )
    better_than = await db.scalar(
        select(func.count()).where(
            PRReview.repo_id == repo.id,
            PRReview.score_overall < 60.0,
        )
    )
    percentile = round((better_than / total) * 100) if total else 0
    assert total == 5
    assert better_than == 2
    assert percentile == 40


async def test_score_boundary_values_stored_correctly(db):
    # Verify that boundary scores (0 and 100) are persisted as-is
    repo = Repository(
        full_name="owner/boundary-repo", owner="owner", name="boundary-repo"
    )
    db.add(repo)
    await db.flush()

    db.add(_make_review(repo.id, "sha-zero", pr_number=1, score=0.0))
    db.add(_make_review(repo.id, "sha-hundred", pr_number=2, score=100.0))
    await db.commit()

    result = await db.execute(
        select(PRReview).where(
            PRReview.repo_id == repo.id, PRReview.head_sha == "sha-zero"
        )
    )
    low = result.scalar_one()
    assert low.score_overall == 0.0

    result2 = await db.execute(
        select(PRReview).where(
            PRReview.repo_id == repo.id, PRReview.head_sha == "sha-hundred"
        )
    )
    high = result2.scalar_one()
    assert high.score_overall == 100.0


async def test_pr_review_cascade_delete(db):
    # Deleting a repository should cascade-delete its reviews
    repo = Repository(
        full_name="owner/cascade-repo", owner="owner", name="cascade-repo"
    )
    db.add(repo)
    await db.flush()
    repo_id = repo.id

    db.add(_make_review(repo_id, "sha-cascade", pr_number=1, score=75.0))
    await db.commit()

    await db.delete(repo)
    await db.commit()

    result = await db.execute(
        select(PRReview).where(PRReview.repo_id == repo_id)
    )
    rows = result.scalars().all()
    assert len(rows) == 0
