"""Learning engine — manages institutional memory across sessions."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.ideas import ProductIdea
from src.models.learning import (
    FailureAnalysis,
    FailureReason,
    GraveyardEntry,
    Lesson,
    LessonCategory,
    ValidationStatus,
)


@dataclass
class LearningEngine:
    """Manages the platform's institutional memory.

    Responsibilities:
    - Store and retrieve lessons learned
    - Manage the concept graveyard
    - Track failure patterns
    - Provide context for new sessions from past learnings
    """

    lessons: list[Lesson] = field(default_factory=list)
    graveyard: list[GraveyardEntry] = field(default_factory=list)
    failure_analyses: list[FailureAnalysis] = field(default_factory=list)

    def record_lesson(self, lesson: Lesson) -> None:
        """Store a new lesson."""
        self.lessons.append(lesson)

    def archive_concept(
        self,
        idea: ProductIdea,
        session_id: str,
        failure_phase: str,
        failure_reason: FailureReason,
        failure_detail: str,
        judge_score: int = 0,
        salvaged_components: list[str] | None = None,
        resurrection_conditions: str = "",
    ) -> GraveyardEntry:
        """Send a failed concept to the graveyard with full context."""
        entry = GraveyardEntry(
            session_id=session_id,
            concept_name=idea.name,
            elevator_pitch=idea.elevator_pitch,
            failure_phase=failure_phase,
            failure_reason=failure_reason,
            failure_detail=failure_detail,
            salvaged_components=salvaged_components or [],
            resurrection_conditions=resurrection_conditions,
            judge_score=judge_score,
        )
        self.graveyard.append(entry)
        return entry

    def record_failure_analysis(self, analysis: FailureAnalysis) -> None:
        """Store a structured post-mortem."""
        self.failure_analyses.append(analysis)

    def get_relevant_lessons(
        self,
        phase: str = "",
        category: LessonCategory | None = None,
        limit: int = 10,
    ) -> list[Lesson]:
        """Retrieve lessons relevant to the current context.

        Prioritises: validated > unvalidated > contradicted,
        then by confidence, then by recency.
        """
        filtered = self.lessons

        if phase:
            filtered = [l for l in filtered if l.phase == phase]
        if category:
            filtered = [l for l in filtered if l.category == category]

        # Sort: validated first, then by confidence, then recency
        status_order = {
            ValidationStatus.SUPPORTED: 0,
            ValidationStatus.UNVALIDATED: 1,
            ValidationStatus.CONTRADICTED: 2,
        }
        filtered.sort(
            key=lambda l: (
                status_order.get(l.validation_status, 1),
                -l.confidence,
                l.created_at.isoformat(),
            )
        )

        return filtered[:limit]

    def get_graveyard_entries(
        self, failure_reason: FailureReason | None = None, limit: int = 20,
    ) -> list[GraveyardEntry]:
        """Browse the concept graveyard, optionally filtered by failure reason."""
        entries = self.graveyard
        if failure_reason:
            entries = [e for e in entries if e.failure_reason == failure_reason]
        return sorted(entries, key=lambda e: e.archived_at, reverse=True)[:limit]

    def get_failure_trends(self) -> dict[str, int]:
        """Analyse failure patterns across all sessions."""
        trends: dict[str, int] = {}
        for entry in self.graveyard:
            key = f"{entry.failure_phase}:{entry.failure_reason.value}"
            trends[key] = trends.get(key, 0) + 1
        return dict(sorted(trends.items(), key=lambda x: -x[1]))

    def build_context_for_session(self, phase: str = "ideation") -> str:
        """Build an institutional knowledge context string for agent prompts.

        This is injected into agent system prompts at the start of each session
        so they benefit from accumulated wisdom.
        """
        lessons = self.get_relevant_lessons(phase=phase, limit=5)
        graveyard_recent = self.graveyard[-5:] if self.graveyard else []
        trends = self.get_failure_trends()

        parts = []

        if lessons:
            parts.append("LESSONS FROM PREVIOUS SESSIONS:")
            for l in lessons:
                status = f"[{l.validation_status.value}]"
                parts.append(f"  - {status} {l.observation} (confidence: {l.confidence:.0%})")

        if graveyard_recent:
            parts.append("\nRECENTLY FAILED CONCEPTS (avoid repeating these):")
            for g in graveyard_recent:
                parts.append(f"  - '{g.concept_name}' failed at {g.failure_phase}: {g.failure_detail[:80]}")

        if trends:
            parts.append("\nCOMMON FAILURE PATTERNS:")
            for pattern, count in list(trends.items())[:3]:
                parts.append(f"  - {pattern}: {count} occurrences")

        return "\n".join(parts) if parts else ""

    def session_learning_summary(self) -> str:
        """Summarise what the system has learned so far."""
        total_lessons = len(self.lessons)
        validated = sum(1 for l in self.lessons if l.validation_status == ValidationStatus.SUPPORTED)
        graveyard_count = len(self.graveyard)
        analyses = len(self.failure_analyses)

        return (
            f"Institutional Memory: {total_lessons} lessons "
            f"({validated} validated), "
            f"{graveyard_count} concepts in graveyard, "
            f"{analyses} failure analyses"
        )
