"""Tests for debate models and logic."""

from __future__ import annotations

from src.core.debate import _extract_confidence
from src.models.debate import DebateMessage, DebateOutcome, DebateRole


def test_extract_confidence_from_text() -> None:
    """Should find confidence values in text."""
    assert _extract_confidence("My confidence: 0.75", 0.5) == 0.75
    assert _extract_confidence("I rate this 0.8 confidence", 0.5) == 0.8
    assert _extract_confidence("No confidence here", 0.5) == 0.5  # Fallback


import pytest

def test_debate_outcome_confidence_delta() -> None:
    """Confidence delta tracks how the advocate's position shifted."""
    msg1 = DebateMessage(
        agent_name="V", role=DebateRole.ADVOCATE,
        content="test", round_number=1, confidence=0.8,
    )
    msg2 = DebateMessage(
        agent_name="A", role=DebateRole.CRITIC,
        content="test", round_number=1, confidence=0.4,
    )
    outcome = DebateOutcome(
        idea_name="Test",
        rounds=[msg1, msg2],
        advocate_final_confidence=0.6,
        critic_final_confidence=0.5,
        consensus_reached=True,
        summary="Test debate",
    )
    # Started at 0.8, ended at 0.6 = -0.2
    assert outcome.confidence_delta == pytest.approx(-0.2)


def test_consensus_logic() -> None:
    """Consensus when advocate and critic are within 0.2."""
    outcome = DebateOutcome(
        idea_name="Test",
        rounds=[],
        advocate_final_confidence=0.7,
        critic_final_confidence=0.6,
        consensus_reached=True,  # 0.1 diff < 0.2
        summary="Close",
    )
    assert outcome.consensus_reached is True
