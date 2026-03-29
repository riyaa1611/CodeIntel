# 🤖 CodeIntel — AI-Powered GitHub PR Review System

CodeIntel is a production-grade GitHub App that automatically reviews Pull Requests using an LLM (DeepSeek R1 via OpenRouter). It analyzes code diffs against linked GitHub Issues, posts structured review comments directly on PRs, sets commit statuses, sends Slack notifications, and tracks analytics over time via a React dashboard.

---

## Architecture

```
GitHub PR Opened
      │
      ▼
FastAPI /webhook/github
  (verify HMAC signature)
      │
      ▼
Celery Task Queue (Redis)
      │
      ▼
Review Pipeline:
  1. Fetch diff + PR details + linked issue
  2. OpenRouter (DeepSeek R1) → structured JSON
  3. Save to PostgreSQL
  4. Post GitHub comment + commit status
  5. Send Slack notification
      │
      ▼
React Dashboard (analytics, leaderboard, PR detail)
```

---

## Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **PostgreSQL** (local Windows installation)
- **Docker Desktop** (for Redis only)
- **ngrok** (for local webhook testing)

---

## Quick Start

### 1. Clone and set up project

```bash
cd codeintel/backend
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Start Redis via Docker

```bash
docker-compose up -d
# Redis will be available at localhost:6379
```

Verify Redis is running:
```bash
docker ps
# or
redis-cli ping  # should respond PONG
```

### 3. Set up PostgreSQL database

Connect to PostgreSQL and create the database:
```sql
CREATE USER codeintel WITH PASSWORD 'codeintel';
CREATE DATABASE codeintel OWNER codeintel;
GRANT ALL PRIVILEGES ON DATABASE codeintel TO codeintel;
```

### 4. Install backend dependencies

```bash
cd codeintel/backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Run database migrations

```bash
cd codeintel/backend
alembic upgrade head
```

This creates the `repositories` and `pr_reviews` tables.

### 6. Start the FastAPI server

```bash
cd codeintel/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: http://localhost:8000/docs

### 7. Start the Celery worker

Open a new terminal:
```bash
cd codeintel/backend
# Activate venv first
celery -A celery_worker worker --loglevel=info --concurrency=2
```

### 8. Start the frontend

```bash
cd codeintel/frontend
npm install
npm run dev
```

Dashboard available at: http://localhost:5173

---

## Registering a GitHub App

### Option A: Personal Access Token (simpler for local dev)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create token with permissions:
   - **Repository permissions:** Contents (read), Pull requests (read/write), Commit statuses (write), Issues (read)
3. Set `GITHUB_TOKEN=ghp_your_token` in `.env`

### Option B: GitHub App (production)

1. Go to GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
2. Fill in:
   - **Homepage URL:** your server URL
   - **Webhook URL:** your ngrok URL + `/webhook/github`
   - **Webhook secret:** a random string (set as `GITHUB_WEBHOOK_SECRET` in `.env`)
3. Permissions needed:
   - Pull requests: Read & Write
   - Contents: Read
   - Issues: Read
   - Commit statuses: Read & Write
4. Subscribe to events: **Pull request**, **Issue comment**
5. Generate and download the private key
6. Install the app on your repository
7. Set in `.env`:
   ```
   GITHUB_APP_ID=12345
   GITHUB_PRIVATE_KEY_PATH=./your-app.pem
   ```

---

## Exposing Webhook via ngrok (Local Testing)

### Install ngrok

Download from https://ngrok.com/download or:
```bash
winget install ngrok
```

### Start tunnel

```bash
ngrok http 8000
```

You'll get a URL like `https://abc123.ngrok-free.app`.

Set this as your GitHub App webhook URL:
```
https://abc123.ngrok-free.app/webhook/github
```

### Test the webhook

```bash
# Install GitHub CLI if needed
gh pr create --title "test: add feature" --body "Closes #1"
```

Watch the FastAPI + Celery logs for the review pipeline running.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT or App token |
| `GITHUB_WEBHOOK_SECRET` | Yes | HMAC secret for webhook verification |
| `DATABASE_URL` | Yes | PostgreSQL async URL |
| `REDIS_URL` | Yes | Redis connection URL |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `OPENROUTER_MODEL` | No | Default: `deepseek/deepseek-r1` |
| `SLACK_WEBHOOK_URL` | No | Global Slack webhook (per-repo overrides available) |
| `LOG_LEVEL` | No | Default: `INFO` |
| `APP_ENV` | No | Default: `development` |

---

## API Reference

### Repositories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/repos` | List all connected repos |
| POST | `/api/repos` | Register a new repo |
| PATCH | `/api/repos/{id}/slack` | Update Slack webhook for a repo |

### Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/repos/{id}/reviews` | Paginated PR reviews (filters: page, limit, min_score, max_score) |
| GET | `/api/repos/{id}/reviews/{rid}` | Single review detail |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/repos/{id}/stats` | Aggregate stats + 30-day trend |
| GET | `/api/repos/{id}/leaderboard` | Per-author leaderboard |
| GET | `/api/repos/{id}/benchmark/{score}` | What percentile a score is |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/github` | GitHub webhook receiver |

---

## Re-triggering a Review

Post a comment on any PR:
```
/codeintel review
```

CodeIntel will re-run the full review pipeline on the current HEAD commit.

---

## Review Score Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Requirement Alignment | 30% | Does the code implement what the issue/PR description requires? |
| Security | 30% | OWASP Top 10, injection flaws, hardcoded secrets, auth issues |
| Code Quality | 20% | Readability, maintainability, code smells, best practices |
| Performance | 20% | N+1 queries, blocking calls, memory leaks, inefficient algorithms |

**Score thresholds:**
- ✅ 80–100: Excellent
- ⚠️ 60–79: Needs attention
- ❌ 0–59: Critical issues

**Commit status:** `success` if overall score ≥ 70, `failure` if < 70.

---

## Project Structure

```
codeintel/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings from env vars
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── api/
│   │   │   ├── webhooks.py      # GitHub webhook handler
│   │   │   └── analytics.py    # REST API for dashboard
│   │   ├── services/
│   │   │   ├── github_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── review_service.py
│   │   │   └── slack_service.py
│   │   └── workers/
│   │       └── tasks.py         # Celery tasks
│   ├── celery_worker.py
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx         # Main dashboard
│   │   │   └── PRDetail.tsx     # Single PR review
│   │   ├── components/
│   │   │   ├── Dashboard.tsx    # Stats + charts
│   │   │   ├── PRTable.tsx      # Paginated review table
│   │   │   ├── RadarChart.tsx   # Spider chart
│   │   │   ├── TrendChart.tsx   # 30-day line chart
│   │   │   ├── Leaderboard.tsx  # Author rankings
│   │   │   ├── BenchmarkBadge.tsx
│   │   │   └── SlackSetup.tsx
│   │   ├── api/client.ts        # Axios API client
│   │   └── types/index.ts       # TypeScript types
│   └── package.json
└── docker-compose.yml           # Redis only
```

---

## Troubleshooting

### Webhook not receiving events
- Ensure ngrok is running and the URL is set correctly in the GitHub App settings
- Check the GitHub App → Advanced → Recent Deliveries for errors
- Verify `GITHUB_WEBHOOK_SECRET` matches exactly

### AI review fails
- Check `OPENROUTER_API_KEY` is valid and has credits
- The model `deepseek/deepseek-r1` requires sufficient context tokens for large diffs
- Check Celery worker logs for the full error

### Database connection errors
- Ensure PostgreSQL is running: `pg_ctl status`
- Verify `DATABASE_URL` uses `postgresql+asyncpg://` prefix
- Check the database and user exist with correct permissions

### Celery tasks not processing
- Ensure Redis is running: `docker ps` or `redis-cli ping`
- Ensure the Celery worker is running with the correct `--app` flag
- Check Redis URL in `.env` matches the running Redis instance

---

## License

MIT
