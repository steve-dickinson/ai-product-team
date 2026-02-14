"""Data models for the learning and fail-fast systems."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class LessonCategory(str, Enum):
    MARKET_INSIGHT = "market_insight"
    TECHNICAL_DISCOVERY = "technical_discovery"
    PROCESS_IMPROVEMENT = "process_improvement"
    ANTI_PATTERN = "anti_pattern"
    STRATEGIC_PIVOT = "strategic_pivot"


class ValidationStatus(str, Enum):
    UNVALIDATED = "unvalidated"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"


class Lesson(BaseModel):
    """A single lesson learned from a session."""
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    session_id: str
    agent_name: str
    phase: str
    category: LessonCategory
    observation: str = Field(description="Specific, falsifiable claim")
    evidence: str = Field(description="What supports this claim?")
    confidence: float = Field(ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FailureReason(str, Enum):
    MARKET_SATURATED = "market_saturated"
    INSUFFICIENT_MARKET = "insufficient_market"
    TECHNICAL_BLOCKER = "technical_blocker"
    REGULATORY_BARRIER = "regulatory_barrier"
    DESIGN_FLAW = "design_flaw"
    LOW_NOVELTY = "low_novelty"
    UNCLEAR_VALUE_PROP = "unclear_value_prop"


class GraveyardEntry(BaseModel):
    """A concept archived in the graveyard with failure analysis."""
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    session_id: str
    concept_name: str
    elevator_pitch: str
    failure_phase: str
    failure_reason: FailureReason
    failure_detail: str = Field(description="Specific explanation of why it failed")
    salvaged_components: list[str] = Field(
        default_factory=list,
        description="Reusable elements extracted from the failure"
    )
    resurrection_conditions: str = Field(
        default="",
        description="What would need to change for this idea to become viable?"
    )
    judge_score: int = 0
    archived_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FailureAnalysis(BaseModel):
    """Structured post-mortem for a failed concept."""
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    session_id: str
    concept_name: str
    root_cause: FailureReason
    decision_trace: list[str] = Field(description="Sequence of decisions that led here")
    counterfactual: str = Field(
        description="What single change might have led to a different outcome?"
    )
    salvageable_work: list[str] = Field(description="Components with standalone value")
    lessons: list[Lesson] = Field(default_factory=list)
    learning_value_score: float = Field(
        ge=0.0, le=1.0,
        description="How much new institutional knowledge did this failure generate?"
    )
