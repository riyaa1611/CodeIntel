import json
import logging
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """FastAPI dependency: returns current User or raises 401."""
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
    """FastAPI dependency: requires admin role or raises 403."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
