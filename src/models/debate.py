"""Data models for structured agent debates."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class DebateRole(str, Enum):
    """Role an agent plays in a debate."""

    ADVOCATE = "advocate"
    CRITIC = "critic"


class DebateMessage(BaseModel):
    """A single message within a debate."""

    agent_name: str
    role: DebateRole
    content: str
    round_number: int
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DebateOutcome(BaseModel):
    """Summary of a completed debate."""

    debate_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    idea_name: str
    rounds: list[DebateMessage]
    advocate_final_confidence: float
    critic_final_confidence: float
    consensus_reached: bool
    summary: str = Field(description="Brief summary of the debate's key points and outcome")

    @property
    def confidence_delta(self) -> float:
        """How much did the advocate's confidence change during debate?"""
        if not self.rounds:
            return 0.0
        first_advocate = next(
            (m for m in self.rounds if m.role == DebateRole.ADVOCATE), None
        )
        if first_advocate is None:
            return 0.0
        return self.advocate_final_confidence - first_advocate.confidence
