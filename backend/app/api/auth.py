import asyncio
import json
import logging
import secrets
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.utils.cache import get_redis_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_TTL = 60 * 60 * 24 * 7  # 7 days


class PreferencesUpdate(BaseModel):
    email_preferences: dict[Literal["review_alerts", "monthly_digest"], bool]


@router.get("/login")
async def login():
    """Redirect to GitHub OAuth."""
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=read:user,user:email"
    )


@router.get("/github/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange OAuth code for GitHub token, upsert user, set session cookie."""
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
        raise HTTPException(status_code=400, detail="OAuth failed — no access token received")

    async with httpx.AsyncClient() as client:
        user_resp, email_resp = await asyncio.gather(
            client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"},
            ),
            client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"},
            ),
        )

    gh_user = user_resp.json()
    emails = email_resp.json() if email_resp.status_code == 200 else []
    primary_email = next(
        (e["email"] for e in emails if isinstance(e, dict) and e.get("primary") and e.get("verified")),
        None,
    )

    # Advisory lock prevents race condition when two users register simultaneously.
    # Lock is scoped to the transaction and released on commit/rollback.
    await db.execute(text("SELECT pg_advisory_xact_lock(1234567890)"))

    total_users = await db.scalar(select(func.count()).select_from(User))
    is_first_user = (total_users == 0)

    result = await db.execute(select(User).where(User.github_id == gh_user["id"]))
    user = result.scalar_one_or_none()

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
    session_data = json.dumps({"user_id": user.id})
    redis = get_redis_connection()
    if redis:
        await redis.setex(f"session:{session_id}", SESSION_TTL, session_data)

    redirect = RedirectResponse(url="/")
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=SESSION_TTL,
        secure=settings.app_env == "production",
    )
    return redirect


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Return current authenticated user or 401."""
    return {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "role": user.role,
        "email_preferences": user.email_preferences,
    }


@router.post("/logout")
async def logout(request: Request):
    """Delete session from Redis and clear cookie."""
    session_id = request.cookies.get("session_id")
    if session_id:
        redis = get_redis_connection()
        if redis:
            await redis.delete(f"session:{session_id}")

    resp = Response(content='{"status": "logged out"}', media_type="application/json")
    resp.delete_cookie("session_id", httponly=True, samesite="lax", path="/")
    return resp


@router.patch("/preferences")
async def update_preferences(
    body: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update email notification preferences for current user."""
    user.email_preferences = {**user.email_preferences, **body.email_preferences}
    await db.commit()
    return {"status": "updated"}
