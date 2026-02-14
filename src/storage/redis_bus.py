"""Redis message bus — real-time inter-agent communication."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from src.core.config import settings


class RedisBus:
    """Async Redis client for real-time messaging between agents.

    Uses Redis Streams for ordered, persistent message delivery
    and standard keys for state management.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._password = password or getattr(settings, "redis_password", "changeme_redis_pwd")
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        self._redis = aioredis.Redis(
            host=self._host,
            port=self._port,
            password=self._password,
            decode_responses=True,
        )
        await self._redis.ping()

    async def disconnect(self) -> None:
        """Close the Redis connection."""
        if self._redis:
            await self._redis.close()

    @property
    def redis(self) -> aioredis.Redis:
        """Get the Redis client."""
        if self._redis is None:
            raise RuntimeError("Not connected — call connect() first")
        return self._redis

    async def publish_message(
        self, stream: str, agent_name: str, content: str, metadata: dict[str, Any] | None = None,
    ) -> str:
        """Publish a message to a Redis Stream.

        Args:
            stream: Stream name (e.g., "phase:ideation")
            agent_name: Who sent this message
            content: The message content
            metadata: Optional extra data

        Returns:
            The message ID assigned by Redis.
        """
        entry = {
            "agent": agent_name,
            "content": content[:10000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            entry["metadata"] = json.dumps(metadata)

        msg_id: str = await self.redis.xadd(stream, entry)
        return msg_id

    async def read_messages(
        self, stream: str, count: int = 100, last_id: str = "0-0",
    ) -> list[dict[str, Any]]:
        """Read messages from a stream.

        Args:
            stream: Stream name
            count: Max messages to read
            last_id: Read messages after this ID (default: from beginning)
        """
        raw = await self.redis.xrange(stream, min=last_id, count=count)
        messages = []
        for msg_id, fields in raw:
            entry = dict(fields)
            entry["_id"] = msg_id
            if "metadata" in entry:
                try:
                    entry["metadata"] = json.loads(entry["metadata"])
                except json.JSONDecodeError:
                    pass
            messages.append(entry)
        return messages

    async def set_state(self, key: str, value: str) -> None:
        """Set a state key (e.g., pipeline status, current phase)."""
        await self.redis.set(key, value)

    async def get_state(self, key: str) -> str | None:
        """Get a state key."""
        result = await self.redis.get(key)
        return str(result) if result else None
