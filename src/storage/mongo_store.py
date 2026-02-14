"""MongoDB storage — persistent audit trail for all system activity."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.core.config import settings


class MongoStore:
    """Async MongoDB client for persisting agent activity.

    Collections:
      - sessions: Top-level run metadata
      - messages: All agent messages (full audit trail)
      - artefacts: Generated deliverables (ideas, evaluations, code)
      - safety_events: Loop detections, kills, budget alerts
      - cost_ledger: Per-call cost records
      - lessons_learned: Cross-session agent insights (Stage 8)
    """

    def __init__(self, uri: str | None = None, database: str | None = None) -> None:
        self._uri = uri or settings.mongodb_uri if hasattr(settings, "mongodb_uri") else (
            "mongodb://admin:changeme_mongo_pwd@localhost:27017"
        )
        self._db_name = database or "ai_rd_team"
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        self._client = AsyncIOMotorClient(self._uri)
        self._db = self._client[self._db_name]
        await self._client.admin.command("ping")

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if self._db is None:
            raise RuntimeError("Not connected — call connect() first")
        return self._db

    async def save_session(self, session_data: dict[str, Any]) -> str:
        """Save or update a session record."""
        session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.db.sessions.insert_one(session_data)
        return str(result.inserted_id)

    async def save_message(self, message: dict[str, Any]) -> str:
        """Save an agent message to the audit trail."""
        message["saved_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.db.messages.insert_one(message)
        return str(result.inserted_id)

    async def save_artefact(self, artefact: dict[str, Any]) -> str:
        """Save a generated artefact (idea, evaluation, code, etc.)."""
        artefact["saved_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.db.artefacts.insert_one(artefact)
        return str(result.inserted_id)

    async def save_safety_event(self, event: dict[str, Any]) -> str:
        """Save a safety event (loop, budget, kill)."""
        result = await self.db.safety_events.insert_one(event)
        return str(result.inserted_id)

    async def save_cost_entry(self, entry: dict[str, Any]) -> str:
        """Save a cost ledger entry."""
        result = await self.db.cost_ledger.insert_one(entry)
        return str(result.inserted_id)

    async def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve all messages for a session, ordered by timestamp."""
        cursor = self.db.messages.find(
            {"session_id": session_id}
        ).sort("saved_at", 1)
        return await cursor.to_list(length=1000)

    async def get_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions."""
        cursor = self.db.sessions.find().sort("updated_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
