"""Data models for the Judge's evaluations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class IdeaScore(BaseModel):
    """Score for a single product idea, produced by the Judge."""

    idea_id: str
    idea_name: str
    novelty: int = Field(ge=1, le=10, description="How original is this idea? 1=copycat, 10=breakthrough")
    market_potential: int = Field(ge=1, le=10, description="Size and accessibility of the market")
    feasibility: int = Field(ge=1, le=10, description="Can a small team build this in 1-3 months?")
    clarity: int = Field(ge=1, le=10, description="How well-defined is the problem and solution?")
    overall: int = Field(ge=1, le=10, description="Overall viability score")
    reasoning: str = Field(description="Brief explanation of the scores")
    pass_gate: bool = Field(description="Does this idea pass to the next phase?")

    @property
    def average_score(self) -> float:
        """Calculate the mean of the four sub-scores."""
        return (self.novelty + self.market_potential + self.feasibility + self.clarity) / 4


class EvaluationReport(BaseModel):
    """Complete evaluation report for a batch of ideas."""

    evaluation_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    session_id: str
    scores: list[IdeaScore]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: str = "gpt-4o-mini"
    gate_threshold: int = 7
