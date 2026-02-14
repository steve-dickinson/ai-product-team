"""Tests for the learning engine."""

from __future__ import annotations

from src.core.learning_engine import LearningEngine
from src.models.ideas import ProductIdea
from src.models.learning import (
    FailureReason,
    Lesson,
    LessonCategory,
    ValidationStatus,
)


def test_record_and_retrieve_lessons() -> None:
    engine = LearningEngine()
    lesson = Lesson(
        session_id="s1", agent_name="Test", phase="ideation",
        category=LessonCategory.MARKET_INSIGHT,
        observation="Test observation", evidence="Test evidence",
        confidence=0.8,
    )
    engine.record_lesson(lesson)
    retrieved = engine.get_relevant_lessons(phase="ideation")
    assert len(retrieved) == 1
    assert retrieved[0].observation == "Test observation"


def test_graveyard_archiving() -> None:
    engine = LearningEngine()
    idea = ProductIdea(
        name="Dead Idea", elevator_pitch="Test", target_audience="Test",
        value_proposition="Test", problem_statement="Test", confidence=0.5,
    )
    entry = engine.archive_concept(
        idea=idea, session_id="s1", failure_phase="ideation",
        failure_reason=FailureReason.MARKET_SATURATED,
        failure_detail="Too many competitors",
    )
    assert entry.concept_name == "Dead Idea"
    assert len(engine.graveyard) == 1


def test_failure_trends() -> None:
    engine = LearningEngine()
    idea = ProductIdea(
        name="Test", elevator_pitch="T", target_audience="T",
        value_proposition="T", problem_statement="T", confidence=0.5,
    )
    for _ in range(3):
        engine.archive_concept(
            idea=idea, session_id="s1", failure_phase="feasibility",
            failure_reason=FailureReason.TECHNICAL_BLOCKER,
            failure_detail="Test",
        )
    trends = engine.get_failure_trends()
    assert "feasibility:technical_blocker" in trends
    assert trends["feasibility:technical_blocker"] == 3


def test_build_context_includes_lessons_and_graveyard() -> None:
    engine = LearningEngine()
    engine.record_lesson(Lesson(
        session_id="s1", agent_name="V", phase="ideation",
        category=LessonCategory.MARKET_INSIGHT,
        observation="Test insight", evidence="Evidence", confidence=0.9,
    ))
    context = engine.build_context_for_session(phase="ideation")
    assert "Test insight" in context


def test_validated_lessons_rank_higher() -> None:
    engine = LearningEngine()
    engine.record_lesson(Lesson(
        session_id="s1", agent_name="V", phase="ideation",
        category=LessonCategory.MARKET_INSIGHT,
        observation="Unvalidated", evidence="E", confidence=0.9,
        validation_status=ValidationStatus.UNVALIDATED,
    ))
    engine.record_lesson(Lesson(
        session_id="s2", agent_name="V", phase="ideation",
        category=LessonCategory.MARKET_INSIGHT,
        observation="Validated", evidence="E", confidence=0.7,
        validation_status=ValidationStatus.SUPPORTED,
    ))
    results = engine.get_relevant_lessons(phase="ideation")
    assert results[0].observation == "Validated"
