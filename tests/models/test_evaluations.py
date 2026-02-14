"""Tests for evaluation models."""

from __future__ import annotations

import pytest

from src.models.evaluations import EvaluationReport, IdeaScore


def test_idea_score_validates_range() -> None:
    """Scores must be between 1 and 10."""
    with pytest.raises(Exception):
        IdeaScore(
            idea_id="test",
            idea_name="Test",
            novelty=11,  # Out of range!
            market_potential=5,
            feasibility=5,
            clarity=5,
            overall=5,
            reasoning="Test",
            pass_gate=False,
        )


def test_idea_score_average() -> None:
    """Average score should be the mean of sub-scores."""
    score = IdeaScore(
        idea_id="test",
        idea_name="Test",
        novelty=8,
        market_potential=6,
        feasibility=10,
        clarity=4,
        overall=7,
        reasoning="Test",
        pass_gate=True,
    )
    assert score.average_score == 7.0


def test_evaluation_report_tracks_model() -> None:
    """Report should record which model was used."""
    report = EvaluationReport(
        session_id="abc123",
        scores=[],
        model_used="gpt-4o-mini",
    )
    assert report.model_used == "gpt-4o-mini"
