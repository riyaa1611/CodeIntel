# CodeIntel Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance CodeIntel across 6 phases — LLM upgrade to Claude Sonnet 4.5, full test suite, GitHub OAuth auth, real-time WebSocket UX, AI scanning enhancements, and notifications/export.

**Architecture:** Sequential phases. Backend: FastAPI + SQLAlchemy async + Celery + Redis + PostgreSQL. Frontend: React 18 + TypeScript + Vite. Each phase is independently testable. Phases 4–6 assume Phase 3 auth is in place.

**Tech Stack:** Python: `anthropic`, `slowapi`, `pytest`, `pytest-asyncio`, `respx`, `resend`, `reportlab`, `matplotlib`. Frontend: `vitest`, `@testing-library/react`, `msw`, `react-diff-viewer-continued`.

---

## File Map

### Phase 1 — Foundation
| Action | Path |
|---|---|
| Modify | `backend/requirements.txt` |
| Modify | `backend/app/config.py` |
| Modify | `backend/app/services/ai_service.py` |
| Modify | `backend/app/workers/tasks.py` |
| Create | `backend/alembic/versions/003_add_task_failures.py` |
| Modify | `backend/app/models.py` |
| Create | `backend/app/api/admin.py` |
| Modify | `backend/app/main.py` |
| Modify | `backend/app/utils/cache.py` |
| Modify | `backend/app/api/analytics.py` |
| Modify | `backend/app/services/review_service.py` |
| Create | `backend/app/middleware/rate_limit.py` |

### Phase 2 — Test Suite
| Action | Path |
|---|---|
| Create | `backend/tests/__init__.py` |
| Create | `backend/tests/conftest.py` |
| Create | `backend/.env.test` |
| Create | `backend/pytest.ini` |
| Create | `backend/tests/test_webhooks.py` |
| Create | `backend/tests/test_ai_service.py` |
| Create | `backend/tests/test_reviews.py` |
| Create | `backend/tests/test_analytics.py` |
| Create | `backend/tests/test_rate_limiting.py` |
| Create | `frontend/vitest.config.ts` |
| Create | `frontend/src/test/setup.ts` |
| Create | `frontend/src/test/handlers.ts` |
| Create | `frontend/src/utils/__tests__/scoreUtils.test.ts` |
| Create | `frontend/src/components/__tests__/PRTable.test.tsx` |
| Create | `frontend/src/components/__tests__/PublicRepoSearch.test.tsx` |

### Phase 3 — Auth
| Action | Path |
|---|---|
| Create | `backend/alembic/versions/004_add_users.py` |
| Modify | `backend/app/models.py` |
| Modify | `backend/app/schemas.py` |
| Create | `backend/app/api/auth.py` |
| Create | `backend/app/dependencies.py` |
| Modify | `backend/app/main.py` |
| Modify | `backend/app/config.py` |
| Create | `frontend/src/pages/Login.tsx` |
| Create | `frontend/src/contexts/AuthContext.tsx` |
| Modify | `frontend/src/api/client.ts` |
| Modify | `frontend/src/App.tsx` |
| Modify | `frontend/src/pages/Home.tsx` |

### Phase 4 — Real-Time & UX
| Action | Path |
|---|---|
| Create | `backend/app/utils/ws_manager.py` |
| Create | `backend/app/api/websocket.py` |
| Modify | `backend/app/main.py` |
| Modify | `backend/app/workers/tasks.py` |
| Create | `backend/app/api/reviews.py` |
| Modify | `backend/app/api/analytics.py` |
| Create | `frontend/src/hooks/useWebSocket.ts` |
| Create | `frontend/src/contexts/ToastContext.tsx` |
| Create | `frontend/src/components/ToastContainer.tsx` |
| Create | `frontend/src/components/DarkModeToggle.tsx` |
| Create | `frontend/src/components/PRDiffViewer.tsx` |
| Modify | `frontend/src/pages/PRDetail.tsx` |
| Create | `frontend/src/pages/AuthorTrend.tsx` |
| Modify | `frontend/src/App.tsx` |
| Modify | `frontend/index.css` |

### Phase 5 — AI & Scanning Enhancements
| Action | Path |
|---|---|
| Create | `backend/alembic/versions/005_add_repo_config.py` |
| Create | `backend/alembic/versions/006_add_scan_schedules.py` |
| Modify | `backend/app/models.py` |
| Modify | `backend/app/schemas.py` |
| Modify | `backend/app/services/ai_service.py` |
| Modify | `backend/app/services/review_service.py` |
| Modify | `backend/app/api/analytics.py` |
| Modify | `backend/app/api/deep_scan.py` |
| Modify | `backend/app/workers/tasks.py` |
| Create | `frontend/src/components/ScoringWeightsSliders.tsx` |
| Create | `frontend/src/components/ScanScheduler.tsx` |
| Modify | `frontend/src/pages/Home.tsx` |

### Phase 6 — Notifications & Export
| Action | Path |
|---|---|
| Modify | `backend/requirements.txt` |
| Modify | `backend/app/config.py` |
| Create | `backend/app/services/email_service.py` |
| Modify | `backend/app/workers/tasks.py` |
| Create | `backend/app/api/export.py` |
| Modify | `backend/app/main.py` |
| Modify | `frontend/src/api/client.ts` |
| Create | `frontend/src/components/ExportPanel.tsx` |
| Create | `frontend/src/components/NotificationPreferences.tsx` |
| Modify | `frontend/src/pages/Home.tsx` |

---

## Phase 1: Foundation

### Task 1: Install Python dependencies

**Files:** `backend/requirements.txt`

- [ ] **Step 1: Add new dependencies**

Replace the contents of `backend/requirements.txt`:

```
fastapi==0.135.1
uvicorn[standard]==0.42.0
celery==5.6.2
celery[redis]==5.6.2
redis==7.3.0
sqlalchemy==2.0.48
asyncpg==0.31.0
alembic==1.18.4
PyGithub==2.9.0
httpx==0.28.1
python-dotenv==1.2.2
pydantic==2.12.5
pydantic-settings==2.13.1
python-multipart==0.0.22
PyJWT==2.12.1
cryptography==46.0.5
anthropic==0.40.0
slowapi==0.1.9
pytest==8.3.2
pytest-asyncio==0.23.8
respx==0.21.1
factory-boy==3.3.1
resend==2.4.0
reportlab==4.2.5
matplotlib==3.9.2
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend && pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add anthropic, slowapi, test, email, pdf dependencies"
```

---

### Task 2: Add new config fields

**Files:** `backend/app/config.py`

- [ ] **Step 1: Add Anthropic and session fields to Settings**

Edit `backend/app/config.py` — add after the `openrouter_model` line:

```python
    # Anthropic (replaces OpenRouter for LLM calls)
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-5", env="ANTHROPIC_MODEL")

    # Auth sessions
    session_secret: str = Field(default="change-me-in-production", env="SESSION_SECRET")

    # Email (Resend)
    resend_api_key: str = Field(default="", env="RESEND_API_KEY")
    email_from: str = Field(default="codeintel@yourdomain.com", env="EMAIL_FROM")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/config.py
git commit -m "chore: add anthropic, session, email config fields"
```

---

### Task 3: Migrate ai_service.py to Anthropic SDK

**Files:** `backend/app/services/ai_service.py`

- [ ] **Step 1: Rewrite ai_service.py**

```python
import json
import logging
from typing import Any

import anthropic

from app.config import settings
from app.schemas import AIReviewOutput

logger = logging.getLogger(__name__)
MAX_RETRIES = 3

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _build_prompt(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
    weights: dict[str, int] | None = None,
) -> str:
    w = weights or {"requirement": 30, "security": 30, "quality": 20, "performance": 20}
    issue_section = ""
    if linked_issue:
        issue_section = (
            f"\n## Linked GitHub Issue\n"
            f"**Issue #{linked_issue['number']}: {linked_issue['title']}**\n"
            f"{linked_issue.get('body', 'No description provided.')}\n"
        )
    else:
        issue_section = "\n## Linked GitHub Issue\nNo linked issue found.\n"

    return f"""You are CodeIntel, an expert AI code reviewer. Analyze the provided Pull Request and return a structured JSON review.

## Repository
- **Language:** {repo_language}
- **Description:** {repo_description or 'Not provided'}

## Pull Request
**Title:** {pr_title}

**Description:**
{pr_body or 'No description provided.'}
{issue_section}
## Code Diff
```diff
{diff}
```

## Your Task
Review this Pull Request across exactly 4 dimensions and return ONLY valid JSON — no markdown, no code fences, no explanation.

Score each dimension from 0 to 100:
1. **Requirement Alignment (score_requirement):** Does the code implement what the issue/PR description requires?
2. **Security (score_security):** OWASP Top 10, hardcoded secrets, auth/authz issues.
3. **Code Quality (score_quality):** Structure, readability, idioms, code smells.
4. **Performance (score_performance):** N+1 queries, blocking calls, missing indexes.

For score_overall, use weighted average: requirement {w['requirement']}%, security {w['security']}%, quality {w['quality']}%, performance {w['performance']}%.

Return ONLY this JSON:
{{
  "score_overall": <number 0-100>,
  "score_requirement": <number 0-100>,
  "score_security": <number 0-100>,
  "score_quality": <number 0-100>,
  "score_performance": <number 0-100>,
  "feedback_requirement": "<detailed paragraph>",
  "feedback_security": "<detailed paragraph>",
  "feedback_quality": "<detailed paragraph>",
  "feedback_performance": "<detailed paragraph>",
  "critical_issues": ["<issue>", ...],
  "warnings": ["<warning>", ...],
  "test_suggestions": ["<test case>", ...]
}}"""


def _call_anthropic_sync(prompt: str) -> str:
    """Synchronous Anthropic call (used from async via thread or directly)."""
    response = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


async def call_llm_with_retry(prompt: str) -> AIReviewOutput:
    """Call Anthropic API with retry logic on malformed JSON."""
    import asyncio

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Calling Anthropic (model=%s, attempt=%d/%d)",
                        settings.anthropic_model, attempt, MAX_RETRIES)
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, _call_anthropic_sync, prompt)

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)
            review = AIReviewOutput(**parsed)
            logger.info("AI review completed (overall=%.1f)", review.score_overall)
            return review

        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Attempt %d/%d: parse error: %s", attempt, MAX_RETRIES, exc)
            last_error = exc
        except Exception as exc:
            logger.error("Attempt %d/%d: LLM error: %s", attempt, MAX_RETRIES, exc)
            last_error = exc
            if attempt == MAX_RETRIES:
                break

    raise RuntimeError(f"AI review failed after {MAX_RETRIES} attempts. Last: {last_error}")


async def generate_review(
    diff: str,
    pr_title: str,
    pr_body: str,
    linked_issue: dict[str, Any] | None,
    repo_language: str,
    repo_description: str,
    weights: dict[str, int] | None = None,
) -> AIReviewOutput:
    """Build prompt and execute AI review."""
    prompt = _build_prompt(
        diff=diff,
        pr_title=pr_title,
        pr_body=pr_body,
        linked_issue=linked_issue,
        repo_language=repo_language,
        repo_description=repo_description,
        weights=weights,
    )
    return await call_llm_with_retry(prompt)
```

- [ ] **Step 2: Also update the deep scan LLM call in tasks.py**

In `backend/app/workers/tasks.py`, replace the `_run_deep_scan_llm` function:

```python
def _run_deep_scan_llm_sync(owner: str, repo: str, file_contents: dict[str, Any]) -> dict[str, Any]:
    """Synchronous Anthropic call for deep scan (called via executor from async)."""
    import anthropic as _anthropic
    client = _anthropic.Anthropic(api_key=settings.anthropic_api_key)

    sections = []
    for path, content in file_contents.items():
        sections.append(f"### {path}\n```\n{content}\n```")

    prompt = DEEP_SCAN_LLM_PROMPT.format(
        owner=owner,
        repo=repo,
        file_count=len(file_contents),
        file_contents="\n\n".join(sections),
    )

    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Deep scan LLM attempt %d failed: %s", attempt, exc)
        except Exception as exc:
            logger.error("Deep scan LLM attempt %d error: %s", attempt, exc)
            if attempt == 3:
                raise
    raise RuntimeError("Deep scan LLM failed after 3 attempts")


async def _run_deep_scan_llm(owner: str, repo: str, file_contents: dict[str, Any]) -> dict[str, Any]:
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_deep_scan_llm_sync, owner, repo, file_contents)
```

Remove the old `_run_deep_scan_llm` function that used httpx/OpenRouter.

Also add `from app.config import settings` import at top of tasks.py if not already there (it already is via `from app.config import settings`).

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai_service.py backend/app/workers/tasks.py
git commit -m "feat: migrate LLM from OpenRouter/DeepSeek to Anthropic Claude Sonnet 4.5"
```

---

### Task 4: Add TaskFailure model and migration

**Files:** `backend/app/models.py`, `backend/alembic/versions/003_add_task_failures.py`

- [ ] **Step 1: Add TaskFailure model to models.py**

Append to `backend/app/models.py`:

```python
class TaskFailure(Base):
    __tablename__ = "task_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_args: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

- [ ] **Step 2: Write migration 003**

Create `backend/alembic/versions/003_add_task_failures.py`:

```python
"""add task_failures table

Revision ID: 003
Revises: 002
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_failures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(256), nullable=False),
        sa.Column("task_args", JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback_text", sa.Text(), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_failures_failed_at", "task_failures", ["failed_at"])


def downgrade() -> None:
    op.drop_index("ix_task_failures_failed_at", table_name="task_failures")
    op.drop_table("task_failures")
```

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade 002 -> 003, add task_failures table`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models.py backend/alembic/versions/003_add_task_failures.py
git commit -m "feat: add TaskFailure model and migration 003"
```

---

### Task 5: Wire Celery on_failure signal to write TaskFailure rows

**Files:** `backend/app/workers/tasks.py`

- [ ] **Step 1: Add on_failure signal handler at bottom of tasks.py**

Append to `backend/app/workers/tasks.py`:

```python
from celery.signals import task_failure as celery_task_failure
import traceback as tb_module


@celery_task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None,
                    args=None, kwargs=None, traceback=None, einfo=None, **rest):
    """Write failed Celery tasks to task_failures table."""
    task_name = getattr(sender, "name", str(sender))
    error_msg = str(exception) if exception else "Unknown error"
    tb_text = "".join(tb_module.format_tb(traceback)) if traceback else None

    task_args = {}
    if args:
        task_args["args"] = list(args)
    if kwargs:
        task_args["kwargs"] = kwargs

    async def _write():
        from app.database import AsyncSessionLocal
        from app.models import TaskFailure

        async with AsyncSessionLocal() as session:
            failure = TaskFailure(
                task_name=task_name,
                task_args=task_args,
                error_message=error_msg,
                traceback_text=tb_text,
            )
            session.add(failure)
            await session.commit()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_write())
        finally:
            loop.close()
        logger.info("TaskFailure recorded for task: %s", task_name)
    except Exception as exc:
        logger.error("Failed to record TaskFailure: %s", exc)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/workers/tasks.py
git commit -m "feat: write failed Celery tasks to task_failures via signal handler"
```

---

### Task 6: Create admin API endpoints

**Files:** `backend/app/api/admin.py`

- [ ] **Step 1: Create admin.py**

```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models import TaskFailure
from app.workers.tasks import celery_app

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/failures")
async def list_failures(db: AsyncSession = Depends(get_db)):
    """List all failed Celery tasks, newest first."""
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
async def retry_failure(failure_id: int, db: AsyncSession = Depends(get_db)):
    """Re-enqueue a failed task with its original arguments."""
    result = await db.execute(select(TaskFailure).where(TaskFailure.id == failure_id))
    failure = result.scalar_one_or_none()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure not found")

    args = failure.task_args.get("args", [])
    kwargs = failure.task_args.get("kwargs", {})

    task_map = {
        "tasks.process_pr_review": "tasks.process_pr_review",
        "tasks.deep_scan_repository": "tasks.deep_scan_repository",
    }

    if failure.task_name not in task_map:
        raise HTTPException(status_code=400, detail=f"Cannot retry task: {failure.task_name}")

    celery_app.send_task(failure.task_name, args=args, kwargs=kwargs)
    failure.retry_count += 1
    await db.commit()
    return {"status": "queued", "task_name": failure.task_name}
```

- [ ] **Step 2: Mount admin router in main.py**

In `backend/app/main.py`, add to the router imports and mounts:

```python
from app.api.admin import router as admin_router
# ... in the app setup section:
app.include_router(admin_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/admin.py backend/app/main.py
git commit -m "feat: add admin API endpoints for failed task visibility and retry"
```

---

### Task 7: Expand Redis caching

**Files:** `backend/app/utils/cache.py`, `backend/app/api/analytics.py`, `backend/app/services/review_service.py`

- [ ] **Step 1: Add cache_delete and cache_delete_pattern to cache.py**

Append to `backend/app/utils/cache.py`:

```python
async def cache_delete(key: str) -> None:
    """Delete a single cache key."""
    try:
        redis = aioredis.from_url(settings.redis_url)
        await redis.delete(key)
        await redis.aclose()
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all cache keys matching a pattern (uses SCAN, not KEYS)."""
    try:
        redis = aioredis.from_url(settings.redis_url)
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
        await redis.aclose()
    except Exception:
        pass
```

- [ ] **Step 2: Add caching to /stats, /leaderboard, /reviews in analytics.py**

At the top of `backend/app/api/analytics.py`, add the import:

```python
import hashlib
import json as json_mod
from app.utils.cache import cache_get, cache_set
```

In the `get_repo_stats` endpoint, wrap the expensive DB query:

```python
@router.get("/repos/{repo_id}/stats")
async def get_repo_stats(repo_id: int, db: AsyncSession = Depends(get_db)):
    cache_key = f"codeintel:{repo_id}:stats"
    cached = await cache_get(cache_key)
    if cached:
        return json_mod.loads(cached)

    # ... existing DB query logic ...
    result_dict = { ... }  # whatever the endpoint currently returns
    await cache_set(cache_key, json_mod.dumps(result_dict, default=str), ttl=60)
    return result_dict
```

Apply the same pattern to `get_leaderboard` (TTL=300) and `list_reviews` (TTL=30, key includes page+filter hash).

For `list_reviews` cache key:
```python
params_hash = hashlib.md5(
    json_mod.dumps({"page": page, "limit": limit, "min_score": min_score, "max_score": max_score}).encode()
).hexdigest()[:8]
cache_key = f"codeintel:{repo_id}:reviews:{params_hash}"
```

- [ ] **Step 3: Invalidate cache in review_service.py after writing a review**

In `backend/app/services/review_service.py`, after `await session.commit()`:

```python
from app.utils.cache import cache_delete, cache_delete_pattern
# After commit:
await cache_delete(f"codeintel:{repo.id}:stats")
await cache_delete(f"codeintel:{repo.id}:leaderboard")
await cache_delete_pattern(f"codeintel:{repo.id}:reviews:*")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/utils/cache.py backend/app/api/analytics.py backend/app/services/review_service.py
git commit -m "feat: expand Redis caching to stats, leaderboard, reviews with invalidation"
```

---

### Task 8: Add rate limiting middleware

**Files:** `backend/app/middleware/rate_limit.py`, `backend/app/main.py`, `backend/app/api/public.py`, `backend/app/api/deep_scan.py`

- [ ] **Step 1: Create rate_limit.py**

Create `backend/app/middleware/__init__.py` (empty) and `backend/app/middleware/rate_limit.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- [ ] **Step 2: Register limiter in main.py**

In `backend/app/main.py`, add after app creation:

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

- [ ] **Step 3: Apply rate limit to public endpoint**

In `backend/app/api/public.py`, add to the route function:

```python
from fastapi import Request
from app.middleware.rate_limit import limiter

@router.get("/repo/{owner}/{repo}")
@limiter.limit("20/minute")
async def get_public_repo(request: Request, owner: str, repo: str, ...):
    ...
```

- [ ] **Step 4: Apply rate limit to deep scan trigger**

In `backend/app/api/deep_scan.py`:

```python
from fastapi import Request
from app.middleware.rate_limit import limiter

@router.post("/{repo_id}/deep-scan")
@limiter.limit("3/hour")
async def trigger_deep_scan(request: Request, repo_id: int, ...):
    ...
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/middleware/ backend/app/main.py backend/app/api/public.py backend/app/api/deep_scan.py
git commit -m "feat: add slowapi rate limiting (20/min public, 3/hr deep-scan)"
```

---

## Phase 2: Test Suite

### Task 9: Set up pytest infrastructure

**Files:** `backend/tests/`, `backend/pytest.ini`, `backend/.env.test`

- [ ] **Step 1: Create pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
env_files = .env.test
```

- [ ] **Step 2: Create .env.test**

```
DATABASE_URL=postgresql+asyncpg://codeintel:codeintel@localhost:5432/codeintel_test
REDIS_URL=redis://localhost:6379/1
ANTHROPIC_API_KEY=test-key
GITHUB_WEBHOOK_SECRET=test-secret
GITHUB_APP_ID=12345
GITHUB_TOKEN=test-token
OPENROUTER_API_KEY=test-key
```

- [ ] **Step 3: Create tests/conftest.py**

```python
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.config import settings

TEST_DB_URL = settings.database_url


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def db(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
```

- [ ] **Step 4: Create test DB**

```bash
createdb codeintel_test
cd backend && alembic upgrade head
```

Expected: migrations run on test DB.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/ backend/pytest.ini backend/.env.test
git commit -m "test: add pytest infrastructure with async test DB"
```

---

### Task 10: Test webhook HMAC verification

**Files:** `backend/tests/test_webhooks.py`

- [ ] **Step 1: Write failing tests**

```python
import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient
from app.main import app


def make_signature(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


async def test_valid_signature_accepted(client):
    payload = json.dumps({"action": "opened", "pull_request": {"draft": False, "number": 1,
        "title": "Test", "body": "", "user": {"login": "dev"},
        "head": {"sha": "abc123"}, "base": {"ref": "main"}},
        "repository": {"full_name": "owner/repo", "id": 1},
        "installation": {"id": 1}}).encode()
    sig = make_signature(payload, "test-secret")
    response = await client.post("/webhook/github",
        content=payload,
        headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "pull_request",
                 "Content-Type": "application/json"})
    assert response.status_code == 202


async def test_invalid_signature_rejected(client):
    payload = b'{"action": "opened"}'
    response = await client.post("/webhook/github",
        content=payload,
        headers={"X-Hub-Signature-256": "sha256=badsig", "X-GitHub-Event": "pull_request",
                 "Content-Type": "application/json"})
    assert response.status_code == 403


async def test_missing_signature_rejected(client):
    response = await client.post("/webhook/github",
        content=b'{"action": "opened"}',
        headers={"X-GitHub-Event": "pull_request", "Content-Type": "application/json"})
    assert response.status_code == 403
```

- [ ] **Step 2: Run tests**

```bash
cd backend && pytest tests/test_webhooks.py -v
```

Expected: All 3 pass (webhook logic already exists, just testing it).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_webhooks.py
git commit -m "test: webhook HMAC verification tests"
```

---

### Task 11: Test AI service parsing and score clamping

**Files:** `backend/tests/test_ai_service.py`

- [ ] **Step 1: Write tests**

```python
import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock
from app.services.ai_service import call_llm_with_retry, _build_prompt
from app.schemas import AIReviewOutput


VALID_RESPONSE = {
    "score_overall": 75.0,
    "score_requirement": 80.0,
    "score_security": 70.0,
    "score_quality": 75.0,
    "score_performance": 72.0,
    "feedback_requirement": "Good alignment.",
    "feedback_security": "No critical issues.",
    "feedback_quality": "Clean code.",
    "feedback_performance": "Efficient.",
    "critical_issues": [],
    "warnings": ["Minor: unused variable"],
    "test_suggestions": ["Test edge case X"],
}


def _make_mock_message(content: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg


async def test_valid_json_parsed():
    import json
    with patch("app.services.ai_service._call_anthropic_sync",
               return_value=json.dumps(VALID_RESPONSE)):
        result = await call_llm_with_retry("test prompt")
    assert isinstance(result, AIReviewOutput)
    assert result.score_overall == 75.0


async def test_score_clamped_above_100():
    import json
    over = {**VALID_RESPONSE, "score_overall": 150.0}
    with patch("app.services.ai_service._call_anthropic_sync",
               return_value=json.dumps(over)):
        result = await call_llm_with_retry("test prompt")
    assert result.score_overall == 100.0


async def test_score_clamped_below_0():
    import json
    under = {**VALID_RESPONSE, "score_security": -10.0}
    with patch("app.services.ai_service._call_anthropic_sync",
               return_value=json.dumps(under)):
        result = await call_llm_with_retry("test prompt")
    assert result.score_security == 0.0


async def test_malformed_json_retries_and_raises():
    with patch("app.services.ai_service._call_anthropic_sync",
               return_value="not json at all"):
        with pytest.raises(RuntimeError, match="AI review failed after"):
            await call_llm_with_retry("test prompt")


def test_prompt_includes_weights():
    prompt = _build_prompt("diff", "title", "body", None, "Python", "desc",
                           weights={"requirement": 40, "security": 40, "quality": 10, "performance": 10})
    assert "requirement 40%" in prompt
    assert "security 40%" in prompt
```

- [ ] **Step 2: Run tests**

```bash
cd backend && pytest tests/test_ai_service.py -v
```

Expected: All 5 pass.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_ai_service.py
git commit -m "test: AI service JSON parsing, score clamping, weight injection"
```

---

### Task 12: Test review idempotency and analytics

**Files:** `backend/tests/test_reviews.py`, `backend/tests/test_analytics.py`

- [ ] **Step 1: Write review idempotency tests**

```python
import pytest
from sqlalchemy import select
from app.models import Repository, PRReview


async def test_same_head_sha_updates_existing_review(db):
    repo = Repository(full_name="owner/test-repo", owner="owner", name="test-repo")
    db.add(repo)
    await db.flush()

    review1 = PRReview(
        repo_id=repo.id, pr_number=1, pr_title="PR 1", pr_author="dev",
        head_sha="abc123", score_overall=70.0, score_requirement=70.0,
        score_security=70.0, score_quality=70.0, score_performance=70.0,
    )
    db.add(review1)
    await db.commit()

    # Same head_sha — should update, not insert
    result = await db.execute(
        select(PRReview).where(PRReview.repo_id == repo.id, PRReview.head_sha == "abc123")
    )
    existing = result.scalar_one_or_none()
    assert existing is not None
    existing.score_overall = 85.0
    await db.commit()

    result2 = await db.execute(
        select(PRReview).where(PRReview.repo_id == repo.id, PRReview.head_sha == "abc123")
    )
    rows = result2.scalars().all()
    assert len(rows) == 1
    assert rows[0].score_overall == 85.0


async def test_different_sha_creates_new_review(db):
    repo = Repository(full_name="owner/test-repo2", owner="owner", name="test-repo2")
    db.add(repo)
    await db.flush()

    r1 = PRReview(repo_id=repo.id, pr_number=1, pr_title="PR", pr_author="dev",
                  head_sha="sha-v1", score_overall=60.0, score_requirement=60.0,
                  score_security=60.0, score_quality=60.0, score_performance=60.0)
    r2 = PRReview(repo_id=repo.id, pr_number=1, pr_title="PR", pr_author="dev",
                  head_sha="sha-v2", score_overall=75.0, score_requirement=75.0,
                  score_security=75.0, score_quality=75.0, score_performance=75.0)
    db.add_all([r1, r2])
    await db.commit()

    result = await db.execute(select(PRReview).where(PRReview.repo_id == repo.id))
    rows = result.scalars().all()
    assert len(rows) == 2
```

- [ ] **Step 2: Write benchmark percentile test**

```python
# In test_analytics.py
async def test_benchmark_percentile(db):
    repo = Repository(full_name="owner/bench-repo", owner="owner", name="bench-repo")
    db.add(repo)
    await db.flush()

    scores = [20.0, 40.0, 60.0, 80.0, 100.0]
    for i, score in enumerate(scores):
        db.add(PRReview(
            repo_id=repo.id, pr_number=i+1, pr_title=f"PR {i}",
            pr_author="dev", head_sha=f"sha{i}",
            score_overall=score, score_requirement=score,
            score_security=score, score_quality=score, score_performance=score,
        ))
    await db.commit()

    from sqlalchemy import func
    from sqlalchemy import select as sel
    total = await db.scalar(
        sel(func.count()).where(PRReview.repo_id == repo.id)
    )
    better_than = await db.scalar(
        sel(func.count()).where(
            PRReview.repo_id == repo.id,
            PRReview.score_overall < 60.0
        )
    )
    percentile = round((better_than / total) * 100) if total > 0 else 0
    assert percentile == 40  # 2 out of 5 are below 60
```

- [ ] **Step 3: Run all tests**

```bash
cd backend && pytest tests/test_reviews.py tests/test_analytics.py -v
```

Expected: All pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_reviews.py backend/tests/test_analytics.py
git commit -m "test: review idempotency, benchmark percentile"
```

---

### Task 13: Set up Vitest and frontend tests

**Files:** `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`, `frontend/src/utils/__tests__/scoreUtils.test.ts`

- [ ] **Step 1: Install frontend test dependencies**

```bash
cd frontend && npm install -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom msw jsdom
```

- [ ] **Step 2: Create vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
  resolve: {
    alias: { '@': resolve(__dirname, './src') },
  },
})
```

- [ ] **Step 3: Create src/test/setup.ts**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 4: Write score utility tests**

Create `frontend/src/utils/__tests__/scoreUtils.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { getScoreLevel, getScoreColor, getScoreEmoji } from '@/types/index'

describe('getScoreLevel', () => {
  it('returns high for 70 and above', () => {
    expect(getScoreLevel(70)).toBe('high')
    expect(getScoreLevel(100)).toBe('high')
  })
  it('returns medium for 40-69', () => {
    expect(getScoreLevel(40)).toBe('medium')
    expect(getScoreLevel(69)).toBe('medium')
  })
  it('returns low for below 40', () => {
    expect(getScoreLevel(0)).toBe('low')
    expect(getScoreLevel(39)).toBe('low')
  })
})

describe('getScoreEmoji', () => {
  it('returns checkmark for high scores', () => {
    expect(getScoreEmoji(75)).toBe('✅')
  })
  it('returns warning for medium scores', () => {
    expect(getScoreEmoji(55)).toBe('⚠️')
  })
  it('returns cross for low scores', () => {
    expect(getScoreEmoji(30)).toBe('❌')
  })
})
```

- [ ] **Step 5: Add test script to package.json**

In `frontend/package.json` scripts:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 6: Run tests**

```bash
cd frontend && npm test
```

Expected: score utility tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/vitest.config.ts frontend/src/test/ frontend/src/utils/__tests__/ frontend/package.json
git commit -m "test: vitest setup and score utility tests"
```

---

## Phase 3: GitHub OAuth Authentication

### Task 14: Add User model and migration

**Files:** `backend/app/models.py`, `backend/alembic/versions/004_add_users.py`

- [ ] **Step 1: Add User model to models.py**

Append to `backend/app/models.py`:

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="member")
    email_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False,
        default=lambda: {"review_alerts": True, "monthly_digest": True}
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 2: Write migration 004**

```python
"""add users table

Revision ID: 004
Revises: 003
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("email_preferences", JSONB(), nullable=False,
                  server_default='{"review_alerts": true, "monthly_digest": true}'),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_id"),
    )
    op.create_index("ix_users_github_id", "users", ["github_id"])


def downgrade() -> None:
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_table("users")
```

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade 003 -> 004`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models.py backend/alembic/versions/004_add_users.py
git commit -m "feat: add User model and migration 004"
```

---

### Task 15: Create auth endpoints (GitHub OAuth)

**Files:** `backend/app/api/auth.py`

- [ ] **Step 1: Create auth.py**

```python
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_TTL = 60 * 60 * 24 * 7  # 7 days in seconds


async def _get_redis():
    import redis.asyncio as aioredis
    return aioredis.from_url(settings.redis_url)


@router.get("/login")
async def login():
    """Redirect to GitHub OAuth."""
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=read:user,user:email"
    )


@router.get("/callback")
async def callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    """Exchange OAuth code for token, upsert user, set session cookie."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="OAuth failed — no access token")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
        )
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"},
        )

    gh_user = user_resp.json()
    emails = email_resp.json() if email_resp.status_code == 200 else []
    primary_email = next(
        (e["email"] for e in emails if e.get("primary") and e.get("verified")), None
    )

    result = await db.execute(select(User).where(User.github_id == gh_user["id"]))
    user = result.scalar_one_or_none()

    # First user ever becomes admin
    total = await db.scalar(select(User))
    is_first_user = total is None

    if user is None:
        user = User(
            github_id=gh_user["id"],
            username=gh_user["login"],
            avatar_url=gh_user.get("avatar_url"),
            email=primary_email,
            role="admin" if is_first_user else "member",
        )
        db.add(user)
    else:
        user.username = gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
        if primary_email:
            user.email = primary_email

    await db.commit()
    await db.refresh(user)

    session_id = secrets.token_urlsafe(32)
    session_data = json.dumps({"user_id": user.id, "role": user.role})
    redis = await _get_redis()
    await redis.setex(f"session:{session_id}", SESSION_TTL, session_data)
    await redis.aclose()

    response = RedirectResponse(url="/")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL,
        secure=settings.app_env == "production",
    )
    return response


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    """Return current authenticated user."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis = await _get_redis()
    raw = await redis.get(f"session:{session_id}")
    await redis.aclose()

    if not raw:
        raise HTTPException(status_code=401, detail="Session expired")

    session_data = json.loads(raw)
    result = await db.execute(select(User).where(User.id == session_data["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "role": user.role,
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Delete session and clear cookie."""
    session_id = request.cookies.get("session_id")
    if session_id:
        redis = await _get_redis()
        await redis.delete(f"session:{session_id}")
        await redis.aclose()

    response.delete_cookie("session_id")
    return {"status": "logged out"}
```

- [ ] **Step 2: Create dependencies.py**

```python
import json
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.config import settings


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import redis.asyncio as aioredis
    redis = aioredis.from_url(settings.redis_url)
    raw = await redis.get(f"session:{session_id}")
    await redis.aclose()

    if not raw:
        raise HTTPException(status_code=401, detail="Session expired")

    data = json.loads(raw)
    result = await db.execute(select(User).where(User.id == data["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

- [ ] **Step 3: Mount auth router in main.py**

```python
from app.api.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 4: Protect existing routes with auth**

In each of `analytics.py`, `deep_scan.py`, `preview.py`, add:

```python
from app.dependencies import get_current_user
from app.models import User

# Add to each endpoint signature:
current_user: User = Depends(get_current_user)
```

Admin-only routes (POST /api/repos, DELETE /api/repos/{id}, all /api/admin/*):

```python
from app.dependencies import require_admin
current_user: User = Depends(require_admin)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth.py backend/app/dependencies.py backend/app/main.py backend/app/api/
git commit -m "feat: GitHub OAuth login, session management, route protection"
```

---

### Task 16: Build frontend auth (Login page + AuthContext)

**Files:** `frontend/src/pages/Login.tsx`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`

- [ ] **Step 1: Create AuthContext.tsx**

```tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { apiClient } from '@/api/client'

interface User {
  id: number
  username: string
  avatar_url: string | null
  role: 'admin' | 'member'
}

interface AuthContextType {
  user: User | null
  loading: boolean
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({ user: null, loading: true, logout: async () => {} })

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/auth/me')
      .then(r => setUser(r.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const logout = async () => {
    await apiClient.post('/auth/logout')
    setUser(null)
    window.location.href = '/login'
  }

  return <AuthContext.Provider value={{ user, loading, logout }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
```

- [ ] **Step 2: Create Login.tsx**

```tsx
export default function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-10 flex flex-col items-center gap-6 max-w-sm w-full">
        <div className="text-3xl font-bold text-gray-900 dark:text-white">CodeIntel</div>
        <p className="text-gray-500 dark:text-gray-400 text-center">AI-powered PR reviews for your team</p>
        <a
          href="/auth/login"
          className="flex items-center gap-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-6 py-3 rounded-xl font-semibold hover:opacity-90 transition w-full justify-center"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          Sign in with GitHub
        </a>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Add 401 interceptor to client.ts**

Append to `frontend/src/api/client.ts`:

```typescript
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

- [ ] **Step 4: Update App.tsx with protected routes**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import Home from '@/pages/Home'
import PRDetail from '@/pages/PRDetail'
import Login from '@/pages/Login'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/repos/:repoId/reviews/:reviewId" element={<ProtectedRoute><PRDetail /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
```

- [ ] **Step 5: Add user avatar + logout to Home.tsx header**

In the header section of `frontend/src/pages/Home.tsx`, add after the logo:

```tsx
import { useAuth } from '@/contexts/AuthContext'

const { user, logout } = useAuth()

// In the header JSX:
<div className="flex items-center gap-3 ml-auto">
  {user && (
    <>
      {user.avatar_url && (
        <img src={user.avatar_url} alt={user.username}
          className="w-8 h-8 rounded-full border border-gray-200" />
      )}
      <span className="text-sm text-gray-600 dark:text-gray-300">{user.username}</span>
      <button onClick={logout}
        className="text-sm text-red-500 hover:text-red-700 transition">
        Logout
      </button>
    </>
  )}
</div>
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Login.tsx frontend/src/contexts/AuthContext.tsx frontend/src/api/client.ts frontend/src/App.tsx frontend/src/pages/Home.tsx
git commit -m "feat: GitHub OAuth frontend login, auth context, protected routes"
```

---

## Phase 4: Real-Time & UX

### Task 17: Create WebSocket manager and Redis pub/sub

**Files:** `backend/app/utils/ws_manager.py`

- [ ] **Step 1: Create ws_manager.py**

```python
import asyncio
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        logger.info("WS connected. Total: %d", len(self._connections))

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("WS disconnected. Total: %d", len(self._connections))

    async def broadcast(self, data: dict):
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = WebSocketManager()


async def redis_listener():
    """Subscribe to codeintel:events Redis channel and broadcast to WS clients."""
    import redis.asyncio as aioredis
    from app.config import settings

    redis = aioredis.from_url(settings.redis_url)
    pubsub = redis.pubsub()
    await pubsub.subscribe("codeintel:events")
    logger.info("Redis listener subscribed to codeintel:events")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                await manager.broadcast(data)
            except Exception as exc:
                logger.error("WS broadcast error: %s", exc)
```

- [ ] **Step 2: Create websocket.py endpoint**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.ws_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive ping from client
    except WebSocketDisconnect:
        manager.disconnect(ws)
```

- [ ] **Step 3: Register WS router and start Redis listener in main.py**

In the lifespan context manager in `backend/app/main.py`:

```python
import asyncio
from app.utils.ws_manager import redis_listener
from app.api.websocket import router as ws_router

app.include_router(ws_router)

# In lifespan:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing DB init ...
    listener_task = asyncio.create_task(redis_listener())
    yield
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    # ... existing cleanup ...
```

- [ ] **Step 4: Publish events from Celery tasks**

In `backend/app/workers/tasks.py`, add a sync publish helper (Celery is sync):

```python
def _publish_event(event_type: str, data: dict) -> None:
    """Publish event to Redis pub/sub from sync Celery context."""
    try:
        import redis as sync_redis
        r = sync_redis.from_url(settings.redis_url)
        import json as _json
        r.publish("codeintel:events", _json.dumps({"type": event_type, "data": data}))
        r.close()
    except Exception as exc:
        logger.warning("Failed to publish event %s: %s", event_type, exc)
```

In `process_pr_review`, after the result is computed, add:
```python
_publish_event("review.completed", {
    "repo_full_name": repo_full_name,
    "pr_number": pr_number,
    "score_overall": result["score_overall"],
})
```

In `deep_scan_repository`, publish progress events inside `_run()` after fetching files:
```python
# After selecting files, before LLM call:
_publish_event("scan.progress", {"repo_id": repo_id, "percent": 50, "current_file": "Analyzing..."})
# After saving to DB:
_publish_event("scan.completed", {"repo_id": repo_id, "scan_id": scan_id, "overall_score": scan.overall_score})
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/ws_manager.py backend/app/api/websocket.py backend/app/main.py backend/app/workers/tasks.py
git commit -m "feat: WebSocket manager with Redis pub/sub for real-time events"
```

---

### Task 18: Toast notification system (frontend)

**Files:** `frontend/src/contexts/ToastContext.tsx`, `frontend/src/components/ToastContainer.tsx`

- [ ] **Step 1: Create ToastContext.tsx**

```tsx
import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

export type ToastType = 'success' | 'warning' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
  autoDismiss: number // ms, 0 = manual only
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (type: ToastType, message: string, autoDismiss?: number) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((type: ToastType, message: string, autoDismiss?: number) => {
    const defaults = { success: 5000, info: 5000, warning: 10000, error: 0 }
    const dismiss = autoDismiss ?? defaults[type]
    const id = crypto.randomUUID()
    setToasts(prev => [...prev.slice(-2), { id, type, message, autoDismiss: dismiss }])
    if (dismiss > 0) setTimeout(() => removeToast(id), dismiss)
  }, [removeToast])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
```

- [ ] **Step 2: Create ToastContainer.tsx**

```tsx
import { useToast, Toast } from '@/contexts/ToastContext'
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'

const icons = {
  success: <CheckCircle className="w-5 h-5 text-green-500" />,
  warning: <AlertTriangle className="w-5 h-5 text-amber-500" />,
  error: <XCircle className="w-5 h-5 text-red-500" />,
  info: <Info className="w-5 h-5 text-blue-500" />,
}

const colors = {
  success: 'border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800',
  warning: 'border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800',
  error: 'border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800',
  info: 'border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800',
}

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToast()
  return (
    <div role="alert" aria-live="polite"
      className={`flex items-start gap-3 p-4 rounded-xl border shadow-lg w-80 ${colors[toast.type]}`}>
      {icons[toast.type]}
      <p className="flex-1 text-sm text-gray-800 dark:text-gray-100">{toast.message}</p>
      <button onClick={() => removeToast(toast.id)}
        className="text-gray-400 hover:text-gray-600 transition">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export default function ToastContainer() {
  const { toasts } = useToast()
  return (
    <div className="fixed top-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map(t => <ToastItem key={t.id} toast={t} />)}
    </div>
  )
}
```

- [ ] **Step 3: Add ToastProvider and ToastContainer to App.tsx**

```tsx
import { ToastProvider } from '@/contexts/ToastContext'
import ToastContainer from '@/components/ToastContainer'

// Wrap everything in ToastProvider, add ToastContainer inside:
<ToastProvider>
  <AuthProvider>
    <BrowserRouter>
      <Routes>...</Routes>
    </BrowserRouter>
    <ToastContainer />
  </AuthProvider>
</ToastProvider>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/contexts/ToastContext.tsx frontend/src/components/ToastContainer.tsx frontend/src/App.tsx
git commit -m "feat: toast notification system (stacked, auto-dismiss, accessible)"
```

---

### Task 19: WebSocket hook + wire toasts to events

**Files:** `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create useWebSocket.ts**

```typescript
import { useEffect, useRef, useCallback } from 'react'
import { useToast } from '@/contexts/ToastContext'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const retryDelay = useRef(1000)
  const { addToast } = useToast()

  const handleEvent = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'review.completed') {
      addToast('success',
        `PR #${event.data.pr_number} reviewed — Score: ${Number(event.data.score_overall).toFixed(0)}/100`)
    } else if (event.type === 'scan.completed') {
      addToast('success',
        `Deep scan complete — Overall: ${Number(event.data.overall_score).toFixed(0)}/100`)
    } else if (event.type === 'scan.progress') {
      // progress updates are handled by DeepScanPanel polling, not toasts
    }
  }, [addToast])

  const connect = useCallback(() => {
    ws.current = new WebSocket(WS_URL)

    ws.current.onopen = () => {
      retryDelay.current = 1000
    }

    ws.current.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        handleEvent(event)
      } catch (_) {}
    }

    ws.current.onclose = () => {
      setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30000)
        connect()
      }, retryDelay.current)
    }
  }, [handleEvent])

  useEffect(() => {
    connect()
    const ping = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send('ping')
      }
    }, 30000)
    return () => {
      clearInterval(ping)
      ws.current?.close()
    }
  }, [connect])
}
```

- [ ] **Step 2: Call useWebSocket in Home.tsx**

```tsx
import { useWebSocket } from '@/hooks/useWebSocket'

// Inside Home component:
useWebSocket()
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts frontend/src/pages/Home.tsx
git commit -m "feat: WebSocket hook with exponential backoff reconnect, wired to toasts"
```

---

### Task 20: Dark mode

**Files:** `frontend/index.css`, `frontend/src/components/DarkModeToggle.tsx`

- [ ] **Step 1: Add CSS variables to index.css**

Add at the top of `frontend/index.css`:

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
}

[data-theme="dark"] {
  --bg-primary: #111827;
  --bg-secondary: #1f2937;
  --text-primary: #f9fafb;
  --text-secondary: #9ca3af;
  --border-color: #374151;
}
```

- [ ] **Step 2: Create DarkModeToggle.tsx**

```tsx
import { Sun, Moon } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function DarkModeToggle() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('codeintel-theme')
    if (stored) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('codeintel-theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <button
      onClick={() => setDark(d => !d)}
      className="p-2 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 transition"
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  )
}
```

- [ ] **Step 3: Add DarkModeToggle to Home.tsx header**

```tsx
import DarkModeToggle from '@/components/DarkModeToggle'
// In header JSX, before user avatar:
<DarkModeToggle />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/index.css frontend/src/components/DarkModeToggle.tsx frontend/src/pages/Home.tsx
git commit -m "feat: dark mode with CSS variables, localStorage persistence, system preference"
```

---

### Task 21: PR Diff Viewer

**Files:** `backend/app/api/reviews.py`, `frontend/src/components/PRDiffViewer.tsx`, `frontend/src/pages/PRDetail.tsx`

- [ ] **Step 1: Install react-diff-viewer-continued**

```bash
cd frontend && npm install react-diff-viewer-continued
```

- [ ] **Step 2: Create backend diff endpoint**

Create `backend/app/api/reviews.py`:

```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import PRReview, Repository
from app.services.github_service import get_pr_diff, get_installation_token
from app.dependencies import get_current_user
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repos", tags=["reviews"])


@router.get("/{repo_id}/reviews/{review_id}/diff")
async def get_review_diff(
    repo_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PRReview, Repository)
        .join(Repository, PRReview.repo_id == Repository.id)
        .where(PRReview.id == review_id, PRReview.repo_id == repo_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")

    review, repo = row
    try:
        diff = await get_pr_diff(
            repo_full_name=repo.full_name,
            pr_number=review.pr_number,
            installation_id=0,
        )
    except Exception as exc:
        logger.error("Failed to fetch diff: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to fetch diff from GitHub")

    additions = sum(1 for line in diff.splitlines() if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff.splitlines() if line.startswith('-') and not line.startswith('---'))
    files = diff.count('\ndiff --git')

    return {"diff": diff, "files_changed": files, "additions": additions, "deletions": deletions}
```

- [ ] **Step 3: Mount reviews router in main.py**

```python
from app.api.reviews import router as reviews_router
app.include_router(reviews_router)
```

- [ ] **Step 4: Create PRDiffViewer.tsx**

```tsx
import { useState, useEffect } from 'react'
import ReactDiffViewer from 'react-diff-viewer-continued'
import { ChevronDown, ChevronRight, GitPullRequest } from 'lucide-react'
import { apiClient } from '@/api/client'

interface DiffData {
  diff: string
  files_changed: number
  additions: number
  deletions: number
}

interface Props {
  repoId: number
  reviewId: number
}

export default function PRDiffViewer({ repoId, reviewId }: Props) {
  const [open, setOpen] = useState(false)
  const [data, setData] = useState<DiffData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    if (data) return
    setLoading(true)
    try {
      const res = await apiClient.get(`/api/repos/${repoId}/reviews/${reviewId}/diff`)
      setData(res.data)
    } catch {
      setError('Failed to load diff')
    } finally {
      setLoading(false)
    }
  }

  const toggle = () => {
    setOpen(o => !o)
    if (!open) load()
  }

  const isDark = document.documentElement.classList.contains('dark')

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <button onClick={toggle}
        className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition text-left">
        <div className="flex items-center gap-2 font-medium text-gray-800 dark:text-gray-200">
          {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <GitPullRequest className="w-4 h-4" />
          Code Diff
        </div>
        {data && (
          <span className="text-xs text-gray-500">
            {data.files_changed} files &nbsp;
            <span className="text-green-600">+{data.additions}</span> &nbsp;
            <span className="text-red-500">-{data.deletions}</span>
          </span>
        )}
      </button>
      {open && (
        <div className="overflow-auto max-h-[600px] text-sm">
          {loading && <p className="p-4 text-gray-500">Loading diff...</p>}
          {error && <p className="p-4 text-red-500">{error}</p>}
          {data && (
            <ReactDiffViewer
              oldValue=""
              newValue={data.diff}
              splitView={false}
              useDarkTheme={isDark}
              hideLineNumbers={false}
            />
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Add PRDiffViewer to PRDetail.tsx**

In the collapsible sections area of PRDetail.tsx, add:

```tsx
import PRDiffViewer from '@/components/PRDiffViewer'

// After feedback sections:
<PRDiffViewer repoId={review.repo_id} reviewId={review.id} />
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/reviews.py backend/app/main.py frontend/src/components/PRDiffViewer.tsx frontend/src/pages/PRDetail.tsx
git commit -m "feat: PR diff viewer with syntax highlighting, lazy-loaded collapsible"
```

---

### Task 22: Author Trend Charts

**Files:** `backend/app/api/analytics.py`, `frontend/src/pages/AuthorTrend.tsx`, `frontend/src/App.tsx`

- [ ] **Step 1: Add author trend endpoint to analytics.py**

```python
@router.get("/repos/{repo_id}/authors/{author}/trend")
async def get_author_trend(
    repo_id: int,
    author: str,
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func, cast
    from sqlalchemy.types import Date

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(PRReview.created_at, Date).label("date"),
            func.avg(PRReview.score_overall).label("overall"),
            func.avg(PRReview.score_requirement).label("requirement"),
            func.avg(PRReview.score_security).label("security"),
            func.avg(PRReview.score_quality).label("quality"),
            func.avg(PRReview.score_performance).label("performance"),
            func.count().label("pr_count"),
        )
        .where(PRReview.repo_id == repo_id, PRReview.pr_author == author,
               PRReview.created_at >= since)
        .group_by(cast(PRReview.created_at, Date))
        .order_by(cast(PRReview.created_at, Date))
    )
    rows = result.all()
    return [
        {
            "date": str(r.date),
            "overall": round(r.overall, 1),
            "requirement": round(r.requirement, 1),
            "security": round(r.security, 1),
            "quality": round(r.quality, 1),
            "performance": round(r.performance, 1),
            "pr_count": r.pr_count,
        }
        for r in rows
    ]
```

- [ ] **Step 2: Create AuthorTrend.tsx**

```tsx
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { apiClient } from '@/api/client'
import { ArrowLeft } from 'lucide-react'

const COLORS = {
  overall: '#6366f1', requirement: '#10b981',
  security: '#ef4444', quality: '#f59e0b', performance: '#3b82f6',
}

export default function AuthorTrend() {
  const { repoId, author } = useParams<{ repoId: string; author: string }>()
  const [data, setData] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!repoId || !author) return
    apiClient.get(`/api/repos/${repoId}/authors/${author}/trend`)
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }, [repoId, author])

  if (loading) return <div className="p-8 text-gray-500">Loading...</div>

  return (
    <div className="max-w-5xl mx-auto p-6">
      <Link to="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to dashboard
      </Link>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        Score Trend — {author}
      </h1>
      <p className="text-gray-500 mb-8">Last 90 days · {data.length} data points</p>

      {data.length === 0 ? (
        <p className="text-gray-400">No reviews found for this author in the last 90 days.</p>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              {Object.entries(COLORS).map(([key, color]) => (
                <Line key={key} type="monotone" dataKey={key} stroke={color}
                  strokeWidth={key === 'overall' ? 2.5 : 1.5}
                  dot={false} name={key.charAt(0).toUpperCase() + key.slice(1)} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Add route in App.tsx**

```tsx
import AuthorTrend from '@/pages/AuthorTrend'

// In Routes:
<Route path="/repos/:repoId/authors/:author" element={<ProtectedRoute><AuthorTrend /></ProtectedRoute>} />
```

- [ ] **Step 4: Make author names clickable in Leaderboard**

In the Leaderboard component, wrap author name in a Link:

```tsx
import { Link } from 'react-router-dom'

<Link to={`/repos/${repoId}/authors/${entry.author}`}
  className="text-blue-600 hover:underline">
  {entry.author}
</Link>
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/analytics.py frontend/src/pages/AuthorTrend.tsx frontend/src/App.tsx
git commit -m "feat: author trend chart with per-dimension 90-day score history"
```

---

## Phase 5: AI & Scanning Enhancements

### Task 23: Custom scoring weights per repo

**Files:** `backend/alembic/versions/005_add_repo_config.py`, `backend/app/models.py`, `backend/app/api/analytics.py`, `backend/app/services/review_service.py`

- [ ] **Step 1: Write migration 005**

```python
"""add repo_config column to repositories

Revision ID: 005
Revises: 004
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "repositories",
        sa.Column(
            "repo_config",
            JSONB(),
            nullable=False,
            server_default='{"weights": {"requirement": 30, "security": 30, "quality": 20, "performance": 20}, "auto_scan_threshold": 60}',
        ),
    )


def downgrade() -> None:
    op.drop_column("repositories", "repo_config")
```

- [ ] **Step 2: Add repo_config column to Repository model**

In `backend/app/models.py`, add to `Repository`:

```python
    repo_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "weights": {"requirement": 30, "security": 30, "quality": 20, "performance": 20},
            "auto_scan_threshold": 60,
        },
    )
```

- [ ] **Step 3: Add GET/PATCH repo config endpoints in analytics.py**

```python
@router.get("/repos/{repo_id}/config")
async def get_repo_config(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo.repo_config


@router.patch("/repos/{repo_id}/config")
async def update_repo_config(
    repo_id: int,
    config: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    weights = config.get("weights", {})
    total = sum(weights.values())
    if weights and total != 100:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 100, got {total}")

    repo.repo_config = {**repo.repo_config, **config}
    await db.commit()
    return repo.repo_config
```

- [ ] **Step 4: Pass weights to ai_service in review_service.py**

In `run_pr_review`, after fetching repo, extract weights and pass to `generate_review`:

```python
weights = repo.repo_config.get("weights") if hasattr(repo, "repo_config") else None
review_output = await generate_review(
    diff=diff, pr_title=pr_title, pr_body=pr_body,
    linked_issue=linked_issue, repo_language=repo_language,
    repo_description=repo_description, weights=weights,
)
```

- [ ] **Step 5: Run migration**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/005_add_repo_config.py backend/app/models.py backend/app/api/analytics.py backend/app/services/review_service.py
git commit -m "feat: custom scoring weights per repo, stored in repo_config JSONB"
```

---

### Task 24: Scheduled deep scans with Celery Beat

**Files:** `backend/alembic/versions/006_add_scan_schedules.py`, `backend/app/models.py`, `backend/app/workers/tasks.py`

- [ ] **Step 1: Write migration 006**

```python
"""add scan_schedules table

Revision ID: 006
Revises: 005
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("frequency", sa.String(32), nullable=False),  # daily, weekly, monthly
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id"),
    )
    op.create_index("ix_scan_schedules_next_run_at", "scan_schedules", ["next_run_at"])


def downgrade() -> None:
    op.drop_index("ix_scan_schedules_next_run_at", table_name="scan_schedules")
    op.drop_table("scan_schedules")
```

- [ ] **Step 2: Add ScanSchedule model to models.py**

```python
from sqlalchemy import Boolean

class ScanSchedule(Base):
    __tablename__ = "scan_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 3: Add Celery Beat task to check and run scheduled scans**

In `backend/app/workers/tasks.py`, update `make_celery()`:

```python
from celery.schedules import crontab

def make_celery():
    from celery import Celery
    app = Celery("codeintel", broker=settings.redis_url, backend=settings.redis_url)
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
        beat_schedule={
            "check-scheduled-scans": {
                "task": "tasks.run_scheduled_scans",
                "schedule": crontab(minute=0),  # every hour
            },
            "send-monthly-digest": {
                "task": "tasks.send_monthly_digest",
                "schedule": crontab(minute=0, hour=9, day_of_month=1),
            },
        },
    )
    return app
```

Add the Beat task:

```python
@celery_app.task(name="tasks.run_scheduled_scans", time_limit=60)
def run_scheduled_scans():
    """Check scan_schedules table and enqueue overdue scans."""
    from datetime import datetime, timezone

    async def _run():
        from app.database import AsyncSessionLocal
        from app.models import ScanSchedule, Repository
        from sqlalchemy import select

        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ScanSchedule, Repository)
                .join(Repository, ScanSchedule.repo_id == Repository.id)
                .where(ScanSchedule.enabled == True, ScanSchedule.next_run_at <= now)
            )
            rows = result.all()

            for schedule, repo in rows:
                logger.info("Enqueuing scheduled scan for %s", repo.full_name)
                celery_app.send_task(
                    "tasks.deep_scan_repository",
                    args=[repo.owner, repo.name, repo.id],
                )
                from datetime import timedelta
                freq_delta = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1),
                              "monthly": timedelta(days=30)}
                schedule.next_run_at = now + freq_delta.get(schedule.frequency, timedelta(days=7))
                schedule.last_run_at = now

            await session.commit()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
```

- [ ] **Step 4: Run migration**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/006_add_scan_schedules.py backend/app/models.py backend/app/workers/tasks.py
git commit -m "feat: scheduled deep scans with Celery Beat, hourly check of scan_schedules"
```

---

### Task 25: Auto-trigger with approval flow

**Files:** `backend/app/workers/tasks.py`, `backend/app/api/deep_scan.py`, `backend/app/services/slack_service.py`

- [ ] **Step 1: Add auto-trigger check in process_pr_review task**

In `process_pr_review`, after the result dict is built, add:

```python
# Auto-trigger deep scan if any dimension below threshold
try:
    async def _check_auto_trigger():
        from app.database import AsyncSessionLocal
        from app.models import Repository, PRReview as PRReviewModel
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            repo_result = await session.execute(
                select(Repository).where(Repository.full_name == repo_full_name)
            )
            repo = repo_result.scalar_one_or_none()
            if not repo:
                return

            threshold = repo.repo_config.get("auto_scan_threshold", 60)
            review_result = await session.execute(
                select(PRReviewModel).where(
                    PRReviewModel.repo_id == repo.id,
                    PRReviewModel.head_sha == head_sha,
                )
            )
            review = review_result.scalar_one_or_none()
            if not review:
                return

            scores = [review.score_requirement, review.score_security,
                      review.score_quality, review.score_performance]
            low_scores = [(dim, score) for dim, score in zip(
                ["Requirement", "Security", "Quality", "Performance"], scores
            ) if score < threshold]

            if low_scores:
                import secrets
                import redis as sync_redis

                token = secrets.token_urlsafe(16)
                r = sync_redis.from_url(settings.redis_url)
                r.setex(
                    f"approve_scan:{token}",
                    3600,
                    f"{repo.id}:{repo.owner}:{repo.name}",
                )
                r.close()

                low_str = ", ".join(f"{d}: {s:.0f}" for d, s in low_scores)
                from app.services.slack_service import send_scan_approval_request
                asyncio.run(send_scan_approval_request(
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    low_scores_str=low_str,
                    approve_token=token,
                ))
                _publish_event("scan.approval_needed", {
                    "repo_id": repo.id,
                    "pr_number": pr_number,
                    "low_scores": [{"dim": d, "score": s} for d, s in low_scores],
                    "approve_token": token,
                })

    loop2 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop2)
    try:
        loop2.run_until_complete(_check_auto_trigger())
    finally:
        loop2.close()
except Exception as exc:
    logger.warning("Auto-trigger check failed: %s", exc)
```

- [ ] **Step 2: Add approve/dismiss endpoints to deep_scan.py**

```python
@router.post("/{repo_id}/deep-scan/approve/{token}")
async def approve_scan(
    repo_id: int,
    token: str,
    current_user: User = Depends(get_current_user),
):
    import redis.asyncio as aioredis
    redis = aioredis.from_url(settings.redis_url)
    raw = await redis.get(f"approve_scan:{token}")
    if not raw:
        raise HTTPException(status_code=404, detail="Token expired or invalid")
    await redis.delete(f"approve_scan:{token}")
    await redis.aclose()

    parts = raw.decode().split(":")
    stored_repo_id, owner, repo_name = int(parts[0]), parts[1], parts[2]
    if stored_repo_id != repo_id:
        raise HTTPException(status_code=403, detail="Token does not match repository")

    celery_app.send_task("tasks.deep_scan_repository", args=[owner, repo_name, repo_id])
    return {"status": "scan_queued"}


@router.post("/{repo_id}/deep-scan/dismiss/{token}")
async def dismiss_scan(repo_id: int, token: str, current_user: User = Depends(get_current_user)):
    import redis.asyncio as aioredis
    redis = aioredis.from_url(settings.redis_url)
    await redis.delete(f"approve_scan:{token}")
    await redis.aclose()
    return {"status": "dismissed"}
```

- [ ] **Step 3: Add send_scan_approval_request to slack_service.py**

```python
async def send_scan_approval_request(
    repo_full_name: str,
    pr_number: int,
    low_scores_str: str,
    approve_token: str,
):
    from app.config import settings
    if not settings.slack_webhook_url:
        return

    import httpx
    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"⚠️ Low Scores Detected — {repo_full_name}"}},
            {"type": "section", "text": {"type": "mrkdwn",
                "text": f"PR #{pr_number} scored low on: *{low_scores_str}*\n\nRun a deep scan to investigate?"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "✅ Approve Scan"},
                 "style": "primary",
                 "url": f"http://localhost:8000/api/repos/0/deep-scan/approve/{approve_token}"},
                {"type": "button", "text": {"type": "plain_text", "text": "❌ Dismiss"},
                 "url": f"http://localhost:8000/api/repos/0/deep-scan/dismiss/{approve_token}"},
            ]}
        ]
    }
    async with httpx.AsyncClient() as client:
        await client.post(settings.slack_webhook_url, json=payload)
```

- [ ] **Step 4: Create ScoringWeightsSliders.tsx**

```tsx
import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import { useToast } from '@/contexts/ToastContext'

interface Weights { requirement: number; security: number; quality: number; performance: number }

export default function ScoringWeightsSliders({ repoId }: { repoId: number }) {
  const [weights, setWeights] = useState<Weights>({ requirement: 30, security: 30, quality: 20, performance: 20 })
  const [saving, setSaving] = useState(false)
  const { addToast } = useToast()
  const total = Object.values(weights).reduce((a, b) => a + b, 0)

  useEffect(() => {
    apiClient.get(`/api/repos/${repoId}/config`)
      .then(r => setWeights(r.data.weights || weights))
      .catch(() => {})
  }, [repoId])

  const save = async () => {
    setSaving(true)
    try {
      await apiClient.patch(`/api/repos/${repoId}/config`, { weights })
      addToast('success', 'Scoring weights saved')
    } catch {
      addToast('error', 'Failed to save weights')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-800 dark:text-gray-200">Scoring Weights</h3>
      {Object.entries(weights).map(([dim, val]) => (
        <div key={dim} className="flex items-center gap-4">
          <span className="w-28 text-sm capitalize text-gray-600 dark:text-gray-400">{dim}</span>
          <input type="range" min={0} max={100} value={val}
            onChange={e => setWeights(w => ({ ...w, [dim]: Number(e.target.value) }))}
            className="flex-1" />
          <span className="w-10 text-sm text-right text-gray-700 dark:text-gray-300">{val}%</span>
        </div>
      ))}
      <div className={`text-sm font-medium ${total === 100 ? 'text-green-600' : 'text-red-500'}`}>
        Total: {total}% {total !== 100 && '(must equal 100)'}
      </div>
      <button onClick={save} disabled={total !== 100 || saving}
        className="px-4 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50 hover:bg-indigo-700 transition text-sm">
        {saving ? 'Saving...' : 'Save Weights'}
      </button>
    </div>
  )
}
```

- [ ] **Step 5: Create ScanScheduler.tsx**

```tsx
import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import { useToast } from '@/contexts/ToastContext'

export default function ScanScheduler({ repoId }: { repoId: number }) {
  const [frequency, setFrequency] = useState('disabled')
  const [saving, setSaving] = useState(false)
  const { addToast } = useToast()

  useEffect(() => {
    apiClient.get(`/api/repos/${repoId}/scan-schedule`)
      .then(r => setFrequency(r.data.frequency || 'disabled'))
      .catch(() => {})
  }, [repoId])

  const save = async () => {
    setSaving(true)
    try {
      await apiClient.post(`/api/repos/${repoId}/scan-schedule`, { frequency })
      addToast('success', frequency === 'disabled' ? 'Schedule disabled' : `Scan scheduled: ${frequency}`)
    } catch {
      addToast('error', 'Failed to save schedule')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-gray-800 dark:text-gray-200">Scheduled Deep Scans</h3>
      <select value={frequency} onChange={e => setFrequency(e.target.value)}
        className="border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200">
        <option value="disabled">Disabled</option>
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>
      <button onClick={save} disabled={saving}
        className="ml-3 px-4 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50 hover:bg-indigo-700 transition text-sm">
        {saving ? 'Saving...' : 'Save Schedule'}
      </button>
    </div>
  )
}
```

- [ ] **Step 6: Add scan-schedule endpoints to deep_scan.py**

```python
@router.get("/{repo_id}/scan-schedule")
async def get_scan_schedule(repo_id: int, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    from app.models import ScanSchedule
    result = await db.execute(select(ScanSchedule).where(ScanSchedule.repo_id == repo_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        return {"frequency": "disabled", "next_run_at": None}
    return {"frequency": schedule.frequency if schedule.enabled else "disabled",
            "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None}


@router.post("/{repo_id}/scan-schedule")
async def set_scan_schedule(repo_id: int, body: dict, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(require_admin)):
    from app.models import ScanSchedule
    from datetime import datetime, timezone, timedelta

    frequency = body.get("frequency", "disabled")
    result = await db.execute(select(ScanSchedule).where(ScanSchedule.repo_id == repo_id))
    schedule = result.scalar_one_or_none()

    if frequency == "disabled":
        if schedule:
            schedule.enabled = False
        await db.commit()
        return {"status": "disabled"}

    freq_delta = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1), "monthly": timedelta(days=30)}
    next_run = datetime.now(timezone.utc) + freq_delta[frequency]

    if schedule:
        schedule.frequency = frequency
        schedule.next_run_at = next_run
        schedule.enabled = True
    else:
        db.add(ScanSchedule(repo_id=repo_id, frequency=frequency, next_run_at=next_run, enabled=True))

    await db.commit()
    return {"status": "scheduled", "frequency": frequency, "next_run_at": next_run.isoformat()}
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/workers/tasks.py backend/app/api/deep_scan.py backend/app/services/slack_service.py frontend/src/components/ScoringWeightsSliders.tsx frontend/src/components/ScanScheduler.tsx
git commit -m "feat: auto-trigger scan with approval flow, scan scheduler, scoring weights UI"
```

---

## Phase 6: Notifications & Export

### Task 26: Email service with Resend

**Files:** `backend/app/services/email_service.py`, `backend/app/workers/tasks.py`

- [ ] **Step 1: Create email_service.py**

```python
import logging
import resend
from app.config import settings

logger = logging.getLogger(__name__)


def _init_resend():
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key


_init_resend()


def send_review_alert(
    to: list[str],
    repo_name: str,
    pr_number: int,
    pr_title: str,
    score_overall: float,
    critical_issues: list[str],
    review_url: str,
) -> None:
    if not settings.resend_api_key or not to:
        return

    issues_html = "".join(f"<li>{issue}</li>" for issue in critical_issues[:5])
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #ef4444;">⚠️ Low Score PR Review — {repo_name}</h2>
      <p><strong>PR #{pr_number}:</strong> {pr_title}</p>
      <p><strong>Overall Score:</strong> <span style="color: #ef4444;">{score_overall:.0f}/100</span></p>
      {'<h3>Critical Issues:</h3><ul>' + issues_html + '</ul>' if critical_issues else ''}
      <a href="{review_url}"
         style="display: inline-block; margin-top: 16px; padding: 10px 20px;
                background: #6366f1; color: white; border-radius: 8px; text-decoration: none;">
        View Full Review
      </a>
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": to,
            "subject": f"[CodeIntel] Low score on PR #{pr_number} in {repo_name} ({score_overall:.0f}/100)",
            "html": html,
        })
        logger.info("Review alert email sent to %d recipients", len(to))
    except Exception as exc:
        logger.error("Failed to send review alert email: %s", exc)


def send_monthly_digest(
    to: list[str],
    repo_name: str,
    month_label: str,
    total_reviews: int,
    avg_score: float,
    top_authors: list[dict],
    top_issues: list[str],
) -> None:
    if not settings.resend_api_key or not to:
        return

    authors_html = "".join(
        f"<tr><td>{a['author']}</td><td>{a['pr_count']}</td><td>{a['avg_score']:.0f}</td></tr>"
        for a in top_authors[:5]
    )
    issues_html = "".join(f"<li>{issue}</li>" for issue in top_issues[:5])

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2>📊 Monthly Code Review Report — {repo_name}</h2>
      <p><strong>Period:</strong> {month_label}</p>
      <h3>Summary</h3>
      <ul>
        <li>Total PRs reviewed: <strong>{total_reviews}</strong></li>
        <li>Average score: <strong>{avg_score:.1f}/100</strong></li>
      </ul>
      <h3>Top Authors</h3>
      <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">
        <tr><th>Author</th><th>PRs</th><th>Avg Score</th></tr>
        {authors_html}
      </table>
      {'<h3>Recurring Issues</h3><ul>' + issues_html + '</ul>' if top_issues else ''}
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": to,
            "subject": f"[CodeIntel] Monthly Report — {month_label} — {repo_name}",
            "html": html,
        })
        logger.info("Monthly digest sent to %d recipients for %s", len(to), repo_name)
    except Exception as exc:
        logger.error("Failed to send monthly digest: %s", exc)
```

- [ ] **Step 2: Trigger review alert after process_pr_review**

In `process_pr_review`, after the result is logged, add:

```python
try:
    async def _send_alert():
        from app.database import AsyncSessionLocal
        from app.models import Repository, PRReview as PRReviewModel, User as UserModel
        from app.services.email_service import send_review_alert
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            repo_result = await session.execute(
                select(Repository).where(Repository.full_name == repo_full_name)
            )
            repo = repo_result.scalar_one_or_none()
            if not repo:
                return

            review_result = await session.execute(
                select(PRReviewModel).where(
                    PRReviewModel.repo_id == repo.id,
                    PRReviewModel.head_sha == head_sha,
                )
            )
            review = review_result.scalar_one_or_none()
            if not review or review.score_overall >= 60:
                return

            users_result = await session.execute(
                select(UserModel).where(
                    UserModel.email.isnot(None),
                )
            )
            users = users_result.scalars().all()
            to = [
                u.email for u in users
                if u.email and u.email_preferences.get("review_alerts", True)
            ]
            if not to:
                return

            send_review_alert(
                to=to,
                repo_name=repo_full_name,
                pr_number=review.pr_number,
                pr_title=review.pr_title,
                score_overall=review.score_overall,
                critical_issues=review.critical_issues or [],
                review_url=f"http://localhost:5173/repos/{repo.id}/reviews/{review.id}",
            )

    loop3 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop3)
    try:
        loop3.run_until_complete(_send_alert())
    finally:
        loop3.close()
except Exception as exc:
    logger.warning("Email alert failed: %s", exc)
```

- [ ] **Step 3: Add monthly digest Celery Beat task**

```python
@celery_app.task(name="tasks.send_monthly_digest", time_limit=120)
def send_monthly_digest_task():
    """Send monthly digest email to all opted-in users for each repo."""
    from datetime import datetime, timezone, timedelta
    import calendar

    async def _run():
        from app.database import AsyncSessionLocal
        from app.models import Repository, PRReview as PRReviewModel, User as UserModel
        from app.services.email_service import send_monthly_digest as _send
        from sqlalchemy import select, func

        now = datetime.now(timezone.utc)
        last_month = now.replace(day=1) - timedelta(days=1)
        month_start = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = last_month.replace(
            day=calendar.monthrange(last_month.year, last_month.month)[1],
            hour=23, minute=59, second=59,
        )
        month_label = last_month.strftime("%B %Y")

        async with AsyncSessionLocal() as session:
            users_result = await session.execute(
                select(UserModel).where(UserModel.email.isnot(None))
            )
            all_users = users_result.scalars().all()
            to = [u.email for u in all_users
                  if u.email and u.email_preferences.get("monthly_digest", True)]
            if not to:
                return

            repos_result = await session.execute(select(Repository))
            repos = repos_result.scalars().all()

            for repo in repos:
                stats = await session.execute(
                    select(func.count(), func.avg(PRReviewModel.score_overall))
                    .where(PRReviewModel.repo_id == repo.id,
                           PRReviewModel.created_at.between(month_start, month_end))
                )
                total, avg = stats.first()
                if not total:
                    continue

                leaderboard = await session.execute(
                    select(PRReviewModel.pr_author,
                           func.count().label("pr_count"),
                           func.avg(PRReviewModel.score_overall).label("avg_score"))
                    .where(PRReviewModel.repo_id == repo.id,
                           PRReviewModel.created_at.between(month_start, month_end))
                    .group_by(PRReviewModel.pr_author)
                    .order_by(func.avg(PRReviewModel.score_overall).desc())
                    .limit(5)
                )
                top_authors = [
                    {"author": r.pr_author, "pr_count": r.pr_count, "avg_score": float(r.avg_score)}
                    for r in leaderboard
                ]

                _send(to=to, repo_name=repo.full_name, month_label=month_label,
                      total_reviews=total, avg_score=float(avg or 0),
                      top_authors=top_authors, top_issues=[])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/email_service.py backend/app/workers/tasks.py
git commit -m "feat: email notifications via Resend (review alerts + monthly digest)"
```

---

### Task 27: CSV and PDF export

**Files:** `backend/app/api/export.py`, `frontend/src/components/ExportPanel.tsx`

- [ ] **Step 1: Create export.py**

```python
import csv
import io
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import PRReview, Repository
from app.dependencies import get_current_user, require_admin
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repos", tags=["export"])


@router.get("/{repo_id}/export/csv")
async def export_reviews_csv(
    repo_id: int,
    from_date: str,
    to_date: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        date_from = datetime.strptime(from_date, "%Y-%m-%d")
        date_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(PRReview)
        .where(PRReview.repo_id == repo_id,
               PRReview.created_at >= date_from,
               PRReview.created_at <= date_to)
        .order_by(PRReview.created_at.desc())
    )
    reviews = result.scalars().all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "pr_number", "pr_title", "pr_author", "head_sha",
            "score_overall", "score_requirement", "score_security",
            "score_quality", "score_performance",
            "critical_issues_count", "warnings_count", "created_at",
        ])
        for r in reviews:
            writer.writerow([
                r.pr_number, r.pr_title, r.pr_author, r.head_sha,
                f"{r.score_overall:.1f}", f"{r.score_requirement:.1f}",
                f"{r.score_security:.1f}", f"{r.score_quality:.1f}",
                f"{r.score_performance:.1f}",
                len(r.critical_issues or []), len(r.warnings or []),
                r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])
        yield output.getvalue()

    filename = f"{repo.name}-reviews-{from_date}-{to_date}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{repo_id}/export/pdf")
async def export_monthly_pdf(
    repo_id: int,
    month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        month_dt = datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    import calendar
    from datetime import timezone
    from sqlalchemy import func

    month_start = month_dt.replace(day=1, tzinfo=timezone.utc)
    month_end = month_dt.replace(
        day=calendar.monthrange(month_dt.year, month_dt.month)[1],
        hour=23, minute=59, second=59, tzinfo=timezone.utc,
    )

    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    reviews_result = await db.execute(
        select(PRReview)
        .where(PRReview.repo_id == repo_id,
               PRReview.created_at.between(month_start, month_end))
        .order_by(PRReview.created_at)
    )
    reviews = reviews_result.scalars().all()

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"CodeIntel Monthly Report", styles["Title"]))
    elements.append(Paragraph(f"{repo.full_name} — {month_dt.strftime('%B %Y')}", styles["Heading2"]))
    elements.append(Spacer(1, 0.5*cm))

    if not reviews:
        elements.append(Paragraph("No reviews found for this month.", styles["Normal"]))
    else:
        avg_overall = sum(r.score_overall for r in reviews) / len(reviews)
        elements.append(Paragraph(f"Total Reviews: {len(reviews)}", styles["Normal"]))
        elements.append(Paragraph(f"Average Score: {avg_overall:.1f}/100", styles["Normal"]))
        elements.append(Spacer(1, 0.5*cm))

        table_data = [["PR #", "Author", "Overall", "Security", "Quality"]]
        for r in reviews[:20]:
            table_data.append([
                f"#{r.pr_number}", r.pr_author,
                f"{r.score_overall:.0f}", f"{r.score_security:.0f}", f"{r.score_quality:.0f}",
            ])

        table = Table(table_data, colWidths=[2*cm, 5*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

    doc.build(elements)
    buf.seek(0)
    filename = f"{repo.name}-report-{month}.pdf"
    return StreamingResponse(
        iter([buf.read()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

- [ ] **Step 2: Mount export router in main.py**

```python
from app.api.export import router as export_router
app.include_router(export_router)
```

- [ ] **Step 3: Create ExportPanel.tsx**

```tsx
import { useState } from 'react'
import { Download, FileText } from 'lucide-react'
import { useToast } from '@/contexts/ToastContext'

export default function ExportPanel({ repoId }: { repoId: number }) {
  const [fromDate, setFromDate] = useState(() => {
    const d = new Date()
    d.setMonth(d.getMonth() - 1)
    return d.toISOString().split('T')[0]
  })
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0])
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7))
  const { addToast } = useToast()

  const downloadCsv = () => {
    window.open(`/api/repos/${repoId}/export/csv?from_date=${fromDate}&to_date=${toDate}`)
  }

  const downloadPdf = () => {
    window.open(`/api/repos/${repoId}/export/pdf?month=${month}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Export CSV</h3>
        <div className="flex items-center gap-3 flex-wrap">
          <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)}
            className="border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200" />
          <span className="text-gray-400">to</span>
          <input type="date" value={toDate} onChange={e => setToDate(e.target.value)}
            className="border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200" />
          <button onClick={downloadCsv}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm">
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Download PDF Report</h3>
        <div className="flex items-center gap-3">
          <input type="month" value={month} onChange={e => setMonth(e.target.value)}
            className="border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200" />
          <button onClick={downloadPdf}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm">
            <FileText className="w-4 h-4" /> Download PDF
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create NotificationPreferences.tsx**

```tsx
import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import { useToast } from '@/contexts/ToastContext'

interface Prefs { review_alerts: boolean; monthly_digest: boolean }

export default function NotificationPreferences() {
  const [prefs, setPrefs] = useState<Prefs>({ review_alerts: true, monthly_digest: true })
  const [saving, setSaving] = useState(false)
  const { addToast } = useToast()

  useEffect(() => {
    apiClient.get('/auth/me').then(r => setPrefs(r.data.email_preferences || prefs)).catch(() => {})
  }, [])

  const save = async () => {
    setSaving(true)
    try {
      await apiClient.patch('/auth/preferences', { email_preferences: prefs })
      addToast('success', 'Notification preferences saved')
    } catch {
      addToast('error', 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-800 dark:text-gray-200">Email Notifications</h3>
      {[
        { key: 'review_alerts', label: 'Low score PR alerts (score < 60)' },
        { key: 'monthly_digest', label: 'Monthly digest report' },
      ].map(({ key, label }) => (
        <label key={key} className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" checked={prefs[key as keyof Prefs]}
            onChange={e => setPrefs(p => ({ ...p, [key]: e.target.checked }))}
            className="w-4 h-4 text-indigo-600" />
          <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
        </label>
      ))}
      <button onClick={save} disabled={saving}
        className="px-4 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50 hover:bg-indigo-700 transition text-sm">
        {saving ? 'Saving...' : 'Save Preferences'}
      </button>
    </div>
  )
}
```

- [ ] **Step 5: Add PATCH /auth/preferences endpoint to auth.py**

```python
@router.patch("/preferences")
async def update_preferences(
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    prefs = body.get("email_preferences", {})
    user.email_preferences = {**user.email_preferences, **prefs}
    await db.commit()
    return {"status": "updated"}
```

- [ ] **Step 6: Add ExportPanel + NotificationPreferences + ScoringWeightsSliders + ScanScheduler to Home.tsx Settings tab**

In the Settings tab JSX of `frontend/src/pages/Home.tsx`:

```tsx
import ExportPanel from '@/components/ExportPanel'
import NotificationPreferences from '@/components/NotificationPreferences'
import ScoringWeightsSliders from '@/components/ScoringWeightsSliders'
import ScanScheduler from '@/components/ScanScheduler'

// In settings tab:
<div className="space-y-8">
  <SlackSetup repoId={selectedRepo.id} />
  <hr className="border-gray-200 dark:border-gray-700" />
  <ScoringWeightsSliders repoId={selectedRepo.id} />
  <hr className="border-gray-200 dark:border-gray-700" />
  <ScanScheduler repoId={selectedRepo.id} />
  <hr className="border-gray-200 dark:border-gray-700" />
  <ExportPanel repoId={selectedRepo.id} />
  <hr className="border-gray-200 dark:border-gray-700" />
  <NotificationPreferences />
</div>
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/export.py backend/app/main.py frontend/src/components/ExportPanel.tsx frontend/src/components/NotificationPreferences.tsx frontend/src/pages/Home.tsx
git commit -m "feat: CSV export, PDF monthly report, notification preferences UI"
```

---

## Final verification

- [ ] **Run all backend tests**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Run all frontend tests**

```bash
cd frontend && npm test
```

Expected: All tests pass.

- [ ] **Verify frontend builds**

```bash
cd frontend && npm run build
```

Expected: No TypeScript errors, build succeeds.

- [ ] **Start services and smoke test**

```bash
# Terminal 1: docker compose up -d
# Terminal 2: cd backend && uvicorn app.main:app --reload
# Terminal 3: cd backend && celery -A app.workers.tasks.celery_app worker --loglevel=info
# Terminal 4: cd backend && celery -A app.workers.tasks.celery_app beat --loglevel=info
# Terminal 5: cd frontend && npm run dev
```

Check: navigate to http://localhost:5173 → login page → GitHub OAuth → dashboard with dark mode toggle, WebSocket toasts, all tabs functional.

- [ ] **Final commit**

```bash
git add -A
git commit -m "feat: complete CodeIntel enhancement (6 phases) — auth, real-time, AI, export"
```
