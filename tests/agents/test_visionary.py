"""Tests for the Visionary agent."""

from __future__ import annotations

from src.models.ideas import IdeaBatch, IdeaStatus, ProductIdea


def test_product_idea_defaults() -> None:
    """Verify ProductIdea sets sensible defaults."""
    idea = ProductIdea(
        name="Test App",
        elevator_pitch="A test app for testing.",
        target_audience="Testers",
        value_proposition="Makes testing easier.",
        problem_statement="Testing is hard.",
        confidence=0.7,
    )
    assert idea.status == IdeaStatus.DRAFT
    assert idea.id  # Should auto-generate
    assert 0.0 <= idea.confidence <= 1.0


def test_idea_batch_requires_at_least_one_idea() -> None:
    """IdeaBatch should reject empty idea lists."""
    import pytest

    with pytest.raises(Exception):  # Pydantic validation error
        IdeaBatch(ideas=[])


def test_idea_batch_accepts_valid_ideas() -> None:
    """IdeaBatch should accept a list of valid ideas."""
    idea = ProductIdea(
        name="Test",
        elevator_pitch="Test pitch.",
        target_audience="Devs",
        value_proposition="Value.",
        problem_statement="Problem.",
        confidence=0.8,
    )
    batch = IdeaBatch(ideas=[idea])
    assert len(batch.ideas) == 1
    assert batch.session_id  # Should auto-generate
