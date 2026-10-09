"""
WebSocket endpoint — real-time event streaming to the frontend.

Clients connect to ``/ws`` and receive JSON events:
  { "type": "review.completed" | "scan.progress" | "scan.completed",
    "repo_id": <int>,
    "data": { ... } }

Authentication: session cookie is validated against Redis on connect.
Unauthenticated connections receive close code 1008 (Policy Violation).
"""

import json
import logging

from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect

from app.utils.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _validate_session(session_id: str) -> bool:
    """Return True if the session_id corresponds to a valid Redis session."""
    from app.utils.cache import get_redis_connection

    redis = get_redis_connection()
    if redis is None:
        return False
    try:
        raw = await redis.get(f"session:{session_id}")
        if not raw:
            return False
        data = json.loads(raw)
        return bool(data.get("user_id"))
    except Exception as exc:
        logger.warning("WS session validation failed: %s", exc)
        return False


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str | None = Cookie(default=None),
) -> None:
    """WebSocket endpoint — session-authenticated; broadcasts live review events."""
    if not session_id or not await _validate_session(session_id):
        await websocket.close(code=1008)  # Policy Violation — not authenticated
        return

    await ws_manager.connect(websocket)
    try:
        # Keep the connection alive; we only push from the server side.
        while True:
            # Drain any client messages (pings/pongs) without crashing.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
