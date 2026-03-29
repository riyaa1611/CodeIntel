"""
Celery worker entry point.
Run with:
    celery -A celery_worker worker --loglevel=info --concurrency=2
"""
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from app.config import settings  # noqa: E402
from app.workers.tasks import celery_app  # noqa: E402, F401

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)
logger.info("CodeIntel Celery worker initialized (broker=%s)", settings.redis_url)
