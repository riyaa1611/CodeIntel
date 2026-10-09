# CodeIntel — Changes Log

## New Features Added

### Feature 1: Instant Public Repository Analytics
Analyze any public GitHub repository by entering `owner/repo` — no webhook or prior connection needed.

### Feature 2: Deep Scan Analysis
AI-powered full codebase analysis across 6 quality dimensions stored as structured results.

### Feature 3: Smart Repository Preview
Auto-display rendered README and detected live deployment URLs for connected repositories.

### Feature 4: Resilient Redis Degradation
Caching utility that silently degrades when Redis is unavailable.

### Feature 5: One-Command Startup (`run.bat`)
Single script to build frontend, install backend deps, and launch the server.

### Feature 6: Swagger Documentation Enhancement
Updated FastAPI app description for accurate API docs.

---

## Files Created (New)

| File | Description |
|------|-------------|
| `backend/app/utils/__init__.py` | Empty package init for the new utils module |
| `backend/app/utils/cache.py` | Resilient async Redis cache helpers (`cache_get`, `cache_set`) with silent degradation |
| `backend/app/api/public.py` | `GET /api/public/repo/{owner}/{repo}` — public GitHub repo analytics with health score and Redis caching |
| `backend/app/api/deep_scan.py` | `POST /api/repos/{id}/deep-scan`, `GET .../latest`, `GET .../history` — deep scan trigger and results retrieval |
| `backend/app/api/preview.py` | `GET /api/repos/{id}/preview` — README markdown + live URL extraction with Redis caching |
| `backend/alembic/versions/002_add_deep_scan_results.py` | Alembic migration adding the `deep_scan_results` table (revision 002, down_revision 001) |
| `frontend/src/components/PublicRepoSearch.tsx` | Search bar + result card for public repo analytics: health score ring, language bar, contributor list |
| `frontend/src/components/DeepScanPanel.tsx` | Deep scan trigger button, polling logic, 6-axis radar chart, findings lists, accordion feedback, sparkline history |
| `frontend/src/components/RepositoryPreview.tsx` | Collapsible panel rendering README with react-markdown + syntax highlighting, live URL cards |
| `run.bat` | One-command Windows startup: builds frontend, installs Python deps, launches uvicorn from `backend/` |

---

## Files Modified (Existing — append-only or targeted additions)

| File | Change |
|------|--------|
| `backend/app/config.py` | Added `github_token: str` field (env: `GITHUB_TOKEN`) for personal access token used in public/deep-scan/preview endpoints |
| `backend/app/models.py` | Appended `DeepScanResult` ORM model class with all score, feedback, and findings columns |
| `backend/app/workers/tasks.py` | Added imports (`httpx`, `base64`, `json`, `re`), helper functions (`_gh_headers`, `_is_excluded_path`, `_is_code_file`, `_score_file`, `_fetch_repo_file_tree`, `_fetch_file_content`, `_run_deep_scan_llm`), constants, and the `deep_scan_repository` Celery task (time_limit=180s) |
| `backend/app/main.py` | Updated FastAPI description; registered `public_router`, `deep_scan_router`, `preview_router`; added static file serving for compiled React frontend (`/assets` mount + SPA catch-all) |
| `frontend/src/types/index.ts` | Appended `ContributorInfo`, `PublicRepoData`, `DeepScanResult`, `DeepScanHistoryItem`, `DeepScanTriggerResponse`, `RepositoryPreview` TypeScript interfaces |
| `frontend/src/api/client.ts` | Appended `getPublicRepo`, `triggerDeepScan`, `getLatestDeepScan`, `getDeepScanHistory`, `getRepoPreview` API functions |
| `frontend/src/pages/Home.tsx` | Added `PublicRepoSearch` section above repo section; added `deep_scan` tab with `DeepScanPanel`; added `RepositoryPreview` to overview tab |
| `frontend/package.json` | Appended `react-markdown ^9.0.1`, `react-syntax-highlighter ^15.5.0` to dependencies; `@types/react-syntax-highlighter ^15.5.11` to devDependencies |
