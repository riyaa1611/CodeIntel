import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, init_db

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CodeIntel API starting up (env=%s)", settings.app_env)
    await init_db()
    yield
    await close_db()
    logger.info("CodeIntel API shut down")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeIntel API",
    description="AI-powered GitHub repository analytics and automated Pull Request review system.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.deep_scan import router as deep_scan_router
from app.api.preview import router as preview_router
from app.api.public import router as public_router
from app.api.webhooks import router as webhooks_router

app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(analytics_router)
app.include_router(public_router)
app.include_router(deep_scan_router)
app.include_router(preview_router)
app.include_router(admin_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    return JSONResponse(content={"status": "ok", "service": "codeintel-api"})


@app.get("/", tags=["system"])
async def root():
    return JSONResponse(
        content={
            "service": "CodeIntel API",
            "version": "1.0.0",
            "docs": "/docs",
        }
    )


# ── Frontend static file serving ──────────────────────────────────────────────
# Mounts the compiled React frontend (npm run build output) so the app can be
# served as a single binary from uvicorn without a separate Node server.
_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="frontend-assets",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the React SPA index.html for all unmatched paths (enables client-side routing)."""
        index_file = _frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"detail": "Frontend not built. Run: npm run build"}, status_code=404)
