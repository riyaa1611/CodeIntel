# CodeIntel Enhancement Design Spec
**Date:** 2026-04-05
**Status:** Approved
**Deployment target:** Render (user deploys manually after testing all 6 phases)
**Team size:** Small team, 2–10 people

---

## Overview

Full enhancement of the CodeIntel AI-powered PR review system across 6 sequential phases. Each phase is independently testable. No deployment until user confirms all phases pass local testing.

---

## LLM Decision

**Selected model:** Claude Sonnet 4.5 via Anthropic SDK directly (user has $20 direct credits).
- Replace `OPENROUTER_API_KEY` + OpenRouter calls with `ANTHROPIC_API_KEY` + `anthropic` Python SDK
- Keep `OPENROUTER_API_KEY` in env as fallback only
- Estimated cost: ~$0.22 per deep scan, ~$0.06 per PR review
- $20 covers ~90 deep scans or ~300 PR reviews — sufficient for months of small team usage

---

## Phase 1 — Foundation

### 1.1 LLM Migration (ai_service.py)
- Replace `httpx` OpenRouter call with `anthropic.Anthropic().messages.create()`
- Model: `claude-sonnet-4-5`
- Keep retry logic (max 3 attempts), JSON parsing, score clamping
- New env var: `ANTHROPIC_API_KEY`
- Remove: `OPENROUTER_API_KEY` dependency from ai_service (keep in .env.example as optional)

### 1.2 Redis Caching Expansion
Extend existing `cache.py` to cover:

| Endpoint | TTL | Invalidation trigger |
|---|---|---|
| `GET /api/repos/{id}/stats` | 60s | New PRReview written |
| `GET /api/repos/{id}/leaderboard` | 300s | New PRReview written |
| `GET /api/repos/{id}/reviews` (per page+filter) | 30s | New PRReview written |

Cache key pattern: `codeintel:{repo_id}:{resource}:{sha256(params)}`

### 1.3 Rate Limiting
Add `slowapi` to FastAPI middleware:

| Route | Limit |
|---|---|
| `GET /api/public/*` | 20/minute per IP |
| `POST /api/repos/*/deep-scan` | 3/hour per repo_id |
| All other `GET /api/*` | 60/minute per IP |
| `POST /webhook/github` | Exempt (GitHub IPs only) |

Return 429 with `Retry-After` header on breach.

### 1.4 Dead Letter Queue
- New migration: `task_failures` table
  - `id`, `task_name`, `task_args` (JSONB), `error_message`, `traceback`, `failed_at`, `retry_count`
- Celery `on_failure` signal writes to this table
- New endpoint: `GET /api/admin/failures` (admin-only after Phase 3; open in Phase 1)
- New endpoint: `POST /api/admin/failures/{id}/retry` — re-enqueues task with original args
- Frontend: "Failed Tasks" section in Settings tab with retry button

---

## Phase 2 — Test Suite

### 2.1 Backend Tests (pytest)
**Setup:**
- `pytest`, `pytest-asyncio`, `httpx`, `respx` (HTTP mocking), `factory-boy` (fixtures)
- Separate test PostgreSQL DB (real DB, no mocks)
- Test env vars in `.env.test`

**Coverage targets:**
| Area | Tests |
|---|---|
| Webhook HMAC verification | Valid sig passes, invalid sig returns 403 |
| AI JSON parsing | Valid JSON parsed correctly, malformed JSON retried, scores clamped 0-100 |
| Review idempotency | Same head_sha updates existing review, new sha creates new row |
| Benchmark percentile | Correct % calculation with known dataset |
| Deep scan file filtering | node_modules excluded, source files included, top 30 selected |
| Rate limiter | 21st request to public endpoint returns 429 |
| Dead letter queue | Failed task writes to task_failures table |
| Cache invalidation | Stats cache cleared after new review saved |

### 2.2 Frontend Tests (Vitest + RTL)
**Setup:**
- `vitest`, `@testing-library/react`, `@testing-library/user-event`, `msw` (API mocking)

**Coverage targets:**
| Component | Tests |
|---|---|
| PRTable | Renders rows, pagination works, filters apply, row click navigates |
| Score utilities | `getScoreColor`, `getScoreEmoji`, `getScoreLevel` boundary values |
| DeepScanPanel | Trigger button calls API, loading state shown, results rendered |
| PublicRepoSearch | Invalid format shows error, API error shows message, results render |
| Toast notifications | Appears on event, auto-dismisses after 5s, max 3 stacked |
| Dark mode toggle | Toggles class on `<html>`, persists to localStorage |

---

## Phase 3 — GitHub OAuth Authentication

### 3.1 Database
New migration adds `users` table:
- `id`, `github_id` (unique), `username`, `avatar_url`, `email`
- `role`: enum `admin` | `member`
- `email_preferences`: JSONB (`{ review_alerts: bool, monthly_digest: bool }`)
- `created_at`

First user to authenticate becomes `admin` automatically.

### 3.2 OAuth Flow
1. `GET /auth/login` → redirect to GitHub OAuth with `client_id` + `scope=read:user,user:email`
2. `GET /auth/callback?code=...` → exchange code for token → fetch GitHub user → upsert `users` row → create Redis session → set `session_id` cookie (HttpOnly, SameSite=Lax, 7-day TTL)
3. `GET /auth/me` → return current user (or 401)
4. `POST /auth/logout` → delete Redis session → clear cookie

**New env vars:** `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SESSION_SECRET`

### 3.3 Authorization
- FastAPI dependency `get_current_user` — reads session cookie, looks up Redis, returns User or raises 401
- FastAPI dependency `require_admin` — asserts role == admin or raises 403
- All `/api/*` routes require `get_current_user`
- Admin-only routes: `POST /api/repos`, `DELETE /api/repos/{id}`, `GET /api/admin/*`, `POST /api/admin/*`

### 3.4 Frontend
- New `/login` route — "Sign in with GitHub" button
- Redirect to `/login` on 401 response (Axios interceptor)
- User avatar + username in header with logout button
- Admin-only UI elements hidden for members (Add Repo button, Settings delete actions)

---

## Phase 4 — Real-Time & UX

### 4.1 WebSocket
- Endpoint: `GET /ws` (upgraded to WebSocket, requires auth cookie)
- Server pushes JSON events:
  ```json
  { "type": "review.completed", "data": { "repo_id": 1, "pr_number": 42, "score_overall": 78.5 } }
  { "type": "scan.progress", "data": { "repo_id": 1, "percent": 45, "current_file": "src/auth.py" } }
  { "type": "scan.completed", "data": { "repo_id": 1, "scan_id": 7, "overall_score": 82.0 } }
  ```
- Celery tasks emit events via Redis pub/sub → FastAPI WebSocket manager broadcasts to subscribed clients
- Frontend reconnects with exponential backoff on disconnect (1s → 2s → 4s → max 30s)

### 4.2 Toast Notifications
- Fixed top-right stack, max 3 visible, FIFO eviction
- Auto-dismiss: 5s (success/info), 10s (warning), manual-only (error)
- Types: success (green), warning (amber), error (red), info (blue)
- Triggered by: WebSocket events, API errors (via Axios interceptor), user actions
- Accessible: `role="alert"`, `aria-live="polite"`

### 4.3 Dark Mode
- CSS custom properties for all color values (`--bg-primary`, `--text-primary`, etc.)
- `<html data-theme="dark|light">` toggled by JS
- localStorage key: `codeintel-theme`
- First visit: respects `prefers-color-scheme` media query
- Toggle button in header (sun/moon icon)
- All Tailwind classes updated to use CSS vars or `dark:` variants

### 4.4 PR Diff Viewer
- New backend endpoint: `GET /api/repos/{repo_id}/reviews/{review_id}/diff`
  - Fetches raw diff from GitHub using stored `head_sha`
  - Returns `{ diff: string, files_changed: number, additions: number, deletions: number }`
- New collapsible section in PRDetail.tsx below feedback sections
- Library: `react-diff-viewer-continued` (fork maintained for React 18)
- Syntax highlighted by file extension, split view on desktop / unified on mobile
- Shows stats bar: X files changed, +Y -Z lines

### 4.5 Author Trend Charts
- New backend endpoint: `GET /api/repos/{repo_id}/authors/{author}/trend?days=90`
  - Returns daily avg scores per dimension for last N days
  - 7-day rolling average applied server-side
- New frontend page: `/repos/:repoId/authors/:author`
- Multi-line chart (Recharts): one line per dimension, hover tooltip
- Accessible from Leaderboard by clicking author name

---

## Phase 5 — AI & Scanning Enhancements

### 5.1 Custom Scoring Weights
- New `repo_config` JSONB column on `repositories` table (migration)
  - Default: `{ "weights": { "requirement": 30, "security": 30, "quality": 20, "performance": 20 } }`
- Settings UI: 4 sliders, live sum displayed, Save disabled if sum ≠ 100
- Weights passed into AI prompt: "Score each dimension and weight the overall as: Requirement X%, Security Y%..."
- `score_overall` recalculated using custom weights before saving

### 5.2 Scheduled Deep Scans
- New `scan_schedules` table: `id`, `repo_id` (unique), `frequency` (daily/weekly/monthly), `next_run_at`, `enabled`, `last_run_at`
- Celery Beat task runs every hour, queries `next_run_at <= now AND enabled = true`, enqueues `deep_scan_repository`
- After scan completes, updates `next_run_at` based on frequency
- Settings UI: dropdown (Disabled / Daily / Weekly / Monthly), toggle switch

### 5.3 Auto-Trigger with Approval
- Config: `auto_scan_threshold` in `repo_config` (default: 60, any dimension score below this triggers)
- After `process_pr_review` saves, checks if any dimension score < threshold
- If triggered: generates one-time approval token (UUID, stored in Redis with 1hr TTL)
- Sends Slack message: "⚠️ Security score: 45/100 on PR #42. Run deep scan? [Approve](URL)"
- In-app toast: same message with Approve/Dismiss buttons
- `POST /api/repos/{id}/deep-scan/approve/{token}` — validates token, enqueues scan, deletes token
- `POST /api/repos/{id}/deep-scan/dismiss/{token}` — deletes token, no scan

---

## Phase 6 — Notifications & Export

### 6.1 Email Notifications (Resend)
- New env var: `RESEND_API_KEY`, `EMAIL_FROM` (e.g. `codeintel@yourdomain.com`)
- Two email templates (HTML):
  1. **Review alert** — triggered when PR score < 60; sent to all users with `review_alerts: true`
     - Subject: `[CodeIntel] Low score on PR #42 in owner/repo (52/100)`
     - Body: score table, critical issues, link to dashboard
  2. **Monthly digest** — Celery Beat task runs on 1st of month at 9am UTC
     - Subject: `[CodeIntel] Monthly Report — March 2026 — owner/repo`
     - Body: trend chart (inline PNG), leaderboard table, top issues this month
- Per-user opt-out managed in Settings → Notification Preferences
- `POST /api/admin/test-email` for admins to test email delivery

### 6.2 CSV Export
- `GET /api/repos/{id}/export/csv?from=YYYY-MM-DD&to=YYYY-MM-DD`
- Streams CSV with columns: pr_number, pr_title, pr_author, score_overall, score_requirement, score_security, score_quality, score_performance, critical_issues_count, created_at
- Frontend: date range picker + "Export CSV" button in PR Reviews tab header
- Filename: `{repo_name}-reviews-{from}-{to}.csv`

### 6.3 PDF Monthly Digest
- `GET /api/repos/{id}/export/pdf?month=YYYY-MM` (admin only)
- Generated with `reportlab` + `matplotlib` (charts rendered to BytesIO PNG, embedded)
- Contents:
  - Cover: repo name, month, generated date
  - Score trend line chart (30 days)
  - Dimension averages radar chart
  - Leaderboard table (top 10 authors)
  - Top 5 critical issues this month
  - Score distribution bar chart
- Returns `application/pdf` with `Content-Disposition: attachment`
- "Download PDF Report" button in Settings tab

---

## Data Model Summary (all migrations)

| Migration | Table | Changes |
|---|---|---|
| 001 | repositories, pr_reviews | Existing |
| 002 | deep_scan_results | Existing |
| 003 | task_failures | Phase 1 |
| 004 | users | Phase 3 |
| 005 | repositories | Add repo_config JSONB column (Phase 5) |
| 006 | scan_schedules | Phase 5 |

---

## Non-Goals (explicitly out of scope)
- Mobile app
- Public SaaS / billing
- GitHub Actions integration
- Outbound webhooks
- Teams notifications
- Grafana / Prometheus monitoring
- Git history analysis (only current PR diff)
