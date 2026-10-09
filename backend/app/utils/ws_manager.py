"""
WebSocket connection manager + Redis pub/sub listener.

Events are published to the Redis channel ``codeintel:events`` as JSON strings.
All connected WebSocket clients receive every event — front-end filters by type.

Event schema:
  { "type": "review.completed" | "scan.progress" | "scan.completed",
    "repo_id": <int>,
    "data": { ... } }
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import WebSocket

from app.utils.cache import get_redis_connection

logger = logging.getLogger(__name__)

EVENTS_CHANNEL = "codeintel:events"


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.debug("WS client connected — total=%d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self._connections.remove(websocket)
        except ValueError:
            pass
        logger.debug("WS client disconnected — total=%d", len(self._connections))

    async def broadcast(self, message: str) -> None:
        """Send a message to every connected client; remove dead connections."""
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Module-level singleton used by both the WebSocket endpoint and the listener.
ws_manager = WebSocketManager()


async def redis_listener() -> None:
    """
    Long-running coroutine that subscribes to the Redis events channel and
    broadcasts every message to all connected WebSocket clients.

    Should be started as a background task in the FastAPI lifespan.
    """
    while True:
        redis = get_redis_connection()
        if redis is None:
            logger.warning("Redis unavailable — WebSocket listener sleeping 10s")
            await asyncio.sleep(10)
            continue

        pubsub = redis.pubsub()
        try:
            await pubsub.subscribe(EVENTS_CHANNEL)
            logger.info("WebSocket listener subscribed to %s", EVENTS_CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message.get("data", "")
                    if data:
                        await ws_manager.broadcast(str(data))
        except asyncio.CancelledError:
            logger.info("WebSocket Redis listener cancelled — shutting down")
            await pubsub.unsubscribe(EVENTS_CHANNEL)
            await pubsub.close()
            return
        except Exception as exc:
            logger.error("WebSocket Redis listener error: %s — reconnecting in 5s", exc)
            await asyncio.sleep(5)
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass


_sync_redis_client = None


def _get_sync_redis():
    """Return a module-level sync Redis client (connection-pooled)."""
    global _sync_redis_client
    if _sync_redis_client is None:
        import redis as sync_redis
        from app.config import settings
        _sync_redis_client = sync_redis.from_url(
            settings.redis_url, decode_responses=True
        )
    return _sync_redis_client


def publish_event_sync(event_type: str, repo_id: int, data: dict) -> None:
    """
    Synchronous helper called from Celery tasks (runs in a regular thread,
    not an async context). Uses a module-level Redis singleton (connection-pooled).
    """
    try:
        payload = json.dumps({"type": event_type, "repo_id": repo_id, "data": data})
        _get_sync_redis().publish(EVENTS_CHANNEL, payload)
    except Exception as exc:
        logger.warning("publish_event_sync failed (%s): %s", event_type, exc)
