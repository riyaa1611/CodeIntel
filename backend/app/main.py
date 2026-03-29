import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    description="AI-powered GitHub PR review system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.analytics import router as analytics_router
from app.api.webhooks import router as webhooks_router

app.include_router(webhooks_router)
app.include_router(analytics_router)


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
