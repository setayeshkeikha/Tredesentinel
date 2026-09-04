"""
Connection manager for the live dashboard feed.

Ticks are published to Redis (channel "ticks") by whichever worker is
running the strategy loop, and every connected WebSocket client — possibly
across multiple API server processes — receives them via a Redis
subscriber. This decouples "who is computing the tick" from "who is
watching it," so the dashboard stays live even under multiple workers.
"""
import asyncio
import json

import redis.asyncio as redis
from fastapi import WebSocket

from app.core.config import settings

TICK_CHANNEL = "tradesentinel:ticks"


class ConnectionManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._redis: redis.Redis | None = None
        self._listener_task: asyncio.Task | None = None

    async def startup(self) -> None:
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._listener_task = asyncio.create_task(self._listen())

    async def shutdown(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        if self._redis:
            await self._redis.close()

    async def _listen(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(TICK_CHANNEL)
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            await self._broadcast(message["data"])

    async def _broadcast(self, payload: str) -> None:
        stale = set()
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.add(ws)
        self._connections -= stale

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def publish_tick(self, data: dict) -> None:
        if self._redis:
            await self._redis.publish(TICK_CHANNEL, json.dumps(data))


manager = ConnectionManager()
