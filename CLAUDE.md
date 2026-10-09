# CodeIntel — Project Context for Claude

## What This Project Is
AI-powered GitHub Pull Request review system. Connects to GitHub via a GitHub App, automatically reviews PRs using an LLM, and provides a React analytics dashboard with leaderboards, trend charts, deep codebase scans, and public repo analytics.

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Celery, Redis, PostgreSQL
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Axios, React Router 6
- **LLM:** Claude Sonnet 4.5 via Anthropic SDK (migrating from DeepSeek R1 via OpenRouter)
- **Auth (planned):** GitHub OAuth, session-based, admin/member roles
- **Deployment target:** Render (PostgreSQL + Redis as Render add-ons)

## Project Structure
```
/backend
  /app
    /api          — route handlers (webhooks, analytics, public, deep_scan, preview)
    /services     — ai_service, github_service, review_service, slack_service
    /workers      — tasks.py (Celery: process_pr_review, deep_scan_repository)
    /utils        — cache.py (Redis wrapper)
    config.py     — Pydantic Settings (env vars)
    database.py   — async SQLAlchemy engine + session
    main.py       — FastAPI app, router mounts, SPA serving
    models.py     — ORM: Repository, PRReview, DeepScanResult
    schemas.py    — Pydantic schemas for API I/O
  /alembic        — DB migrations
  celery_worker.py
/frontend
  /src
    /api          — client.ts (typed Axios wrapper)
    /components   — DeepScanPanel, PublicRepoSearch, RepositoryPreview, etc.
    /pages        — Home.tsx (dashboard), PRDetail.tsx
    /types        — index.ts (TypeScript interfaces + score utilities)
    App.tsx
```

## Database Schema
- `repositories` — registered GitHub repos (full_name, owner, name, slack_webhook_url)
- `pr_reviews` — per-PR AI review (5 dimension scores, JSONB issues/warnings, head_sha for idempotency)
- `deep_scan_results` — codebase scans (6 dimension scores, JSONB findings)
- `task_failures` — dead letter queue for failed Celery tasks (planned Phase 1)

## Score Dimensions
- **PR Review:** Requirement (30%), Security (30%), Quality (20%), Performance (20%)
- **Deep Scan:** Architecture, Security, Duplication, Documentation, Test Coverage → Overall

## Key Behaviors
- PRs are reviewed on `opened`, `synchronize`, `reopened` (not drafts)
- Reviews are **idempotent on head_sha** — pushing new commits replaces the existing review
- `/codeintel review` comment triggers manual re-review
- PR diffs truncated to 50k chars; deep scan fetches top 30 source files (up to 8000 chars each)
- Scores 70+ = GitHub commit status `success`; below 70 = `failure`

## Environment Variables (key ones)
```
GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GITHUB_WEBHOOK_SECRET, GITHUB_TOKEN
DATABASE_URL          # postgresql+asyncpg://...
REDIS_URL             # redis://...
ANTHROPIC_API_KEY     # for Claude Sonnet 4.5 (replacing OPENROUTER_API_KEY)
OPENROUTER_API_KEY    # keep as fallback
SLACK_WEBHOOK_URL     # global default (overridable per repo)
APP_ENV               # development | production
```

## Active Enhancement Plan (6 Phases)
All phases complete before deployment. User deploys to Render manually after testing.

### Phase 1 — Foundation
- LLM: migrate ai_service.py from OpenRouter/DeepSeek to Anthropic SDK / Claude Sonnet 4.5
- Redis caching: expand to /stats, /leaderboard, /reviews endpoints
- Rate limiting: slowapi middleware (20/min public, 3/hr deep-scan, 60/min general)
- Dead letter queue: task_failures table + GET /api/admin/failures + retry in Settings UI

### Phase 2 — Test Suite
- Backend: pytest + pytest-asyncio covering webhook verification, AI parsing, scoring, idempotency
- Frontend: Vitest + React Testing Library for all components and pages

### Phase 3 — Auth
- GitHub OAuth login (no password auth)
- Simple roles: admin (full access) vs member (read-only)
- Sessions stored in Redis
- All /api/* routes require authentication

### Phase 4 — Real-Time & UX
- WebSocket endpoint: push review completion + deep scan progress events
- Toast notifications (Slack-style, top-right corner)
- Dark mode (system preference + manual toggle, persisted in localStorage)
- PR diff viewer in PRDetail.tsx (syntax-highlighted unified diff)
- Author trend charts (individual score trajectory over time)

### Phase 5 — AI & Scanning
- Custom scoring weights per repo (stored in repo_config JSONB column)
- Scheduled deep scans: fixed options (daily/weekly/monthly) in Settings
- Auto-trigger deep scan when PR scores below threshold — sends approval notification before running

### Phase 6 — Notifications & Export
- Email notifications via Resend (team digest + review alerts)
- CSV export of PR reviews (date range filter)
- PDF monthly digest (auto-generated with charts + summaries)

## Coding Conventions
- All backend DB operations use `async/await` with SQLAlchemy async session
- Celery tasks run async pipelines via `asyncio.run()` or event loop
- Cache keys pattern: `codeintel:{repo_id}:{resource}:{params_hash}`
- Pydantic v2 for all schemas; validators clamp scores to 0–100
- Frontend API calls go through `frontend/src/api/client.ts` only — no direct fetch calls in components
- Tailwind CSS for all styling — no inline styles, no CSS modules

## What NOT To Do
- Do not add user-facing features outside the 6-phase plan without asking
- Do not push to remote or deploy — user handles deployment manually
- Do not add backwards-compatibility shims or feature flags
- Do not mock the database in tests — use a real test PostgreSQL instance
- Do not skip webhook HMAC verification in any test or handler
