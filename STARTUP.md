# CodeIntel — Local Startup Guide

Run the app locally with ngrok for GitHub App webhook testing.
You need **5 terminals** running simultaneously.

---

## Prerequisites (one-time)

- Docker Desktop running
- Node.js 18+
- Python 3.11+
- ngrok installed (`npm install -g ngrok` or https://ngrok.com/download)
- ngrok authenticated: `ngrok config add-authtoken <your-token>`

Fill in `.env` before starting:

```
ANTHROPIC_API_KEY=sk-ant-...         # required — LLM won't work without this
RESEND_API_KEY=re_...                # optional — emails silently skip if missing
EMAIL_FROM=codeintel@yourdomain.com  # optional — update to match your Resend domain
```

---

## Terminal 1 — Docker (PostgreSQL + Redis)

```bat
cd D:\CodeIntel
docker-compose up -d
```

Verify both are healthy:

```bat
docker-compose ps
```

Both should show `healthy`. To stop later:

```bat
docker-compose down
```

To wipe all data (full reset):

```bat
docker-compose down -v
```

---

## Terminal 2 — Backend server

Run once on first start (or after pulling new migrations):

```bat
cd D:\CodeIntel\backend
alembic upgrade head
```

Then start the server (also builds the frontend):

```bat
cd D:\CodeIntel
run.bat
```

The API is now available at http://localhost:8000
Swagger docs: http://localhost:8000/docs

---

## Terminal 3 — Celery worker

```bat
cd D:\CodeIntel\backend
celery -A celery_worker worker --loglevel=info --concurrency=2 -P solo
```

`-P solo` avoids Windows multiprocessing issues.

---

## Terminal 4 — Celery Beat (scheduled tasks)

Required for: scheduled deep scans and monthly email digests.

```bat
cd D:\CodeIntel\backend
celery -A celery_worker beat --loglevel=info
```

> **Tip:** You can combine worker + beat in one terminal instead of two:
> ```bat
> celery -A celery_worker worker --beat --loglevel=info --concurrency=2 -P solo
> ```

---

## Terminal 5 — ngrok

```bat
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL from the output.

> If you have a paid ngrok plan with a static domain:
> ```bat
> ngrok http --domain=your-static.ngrok-free.app 8000
> ```

---

## After ngrok starts — update 4 places

### 1. `.env`

```
APP_BASE_URL=https://xxxx.ngrok-free.app
```

Then restart the backend (Ctrl+C in Terminal 2, re-run `run.bat`).

### 2. GitHub App settings → Webhook URL

```
https://xxxx.ngrok-free.app/webhook/github
```

### 3. GitHub App settings → Callback URL

```
https://xxxx.ngrok-free.app/auth/github/callback
```

### 4. GitHub App settings → Homepage URL

```
https://xxxx.ngrok-free.app
```

GitHub App settings: https://github.com/settings/apps

---

## Optional — Frontend dev server (hot reload)

Instead of the built SPA served by FastAPI, run the Vite dev server for hot reload:

```bat
cd D:\CodeIntel\frontend
npm run dev
```

Access the app at http://localhost:5173 — it proxies all `/api`, `/auth`, `/webhook`, and `/ws` calls to the backend at port 8000.

---

## Startup order summary

| Order | Terminal | Command |
|-------|----------|---------|
| 1st | Docker | `docker-compose up -d` |
| 2nd | Backend | `alembic upgrade head` then `run.bat` |
| 3rd | Worker | `celery -A celery_worker worker -P solo` |
| 4th | Beat | `celery -A celery_worker beat` |
| 5th | ngrok | `ngrok http 8000` |

Then update `.env` + GitHub App settings with the ngrok URL, and restart the backend.

---

## Verify everything is working

| Check | URL |
|-------|-----|
| API health | http://localhost:8000/health |
| Swagger docs | http://localhost:8000/docs |
| Frontend (built) | http://localhost:8000 |
| Frontend (dev) | http://localhost:5173 |
| ngrok dashboard | http://localhost:4040 |

Test the webhook by opening a PR on a repo that has the GitHub App installed — you should see the Celery worker pick it up and the review appear in the dashboard.
