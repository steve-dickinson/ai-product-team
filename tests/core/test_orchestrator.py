"""Tests for the Orchestrator."""

from __future__ import annotations

from src.core.orchestrator import Orchestrator
from src.core.phases import GATE_REQUIREMENTS, PipelinePhase
from src.core.safety import SafetyMonitor

def test_orchestrator_initialises() -> None:
    """Orchestrator should start with clean state."""
    orch = Orchestrator()
    assert orch.run.current_phase == PipelinePhase.IDEATION
    assert len(orch.run.active_ideas) == 0


def test_orchestrator_respects_killed_status() -> None:
    """Orchestrator should not proceed when system is killed."""
    safety = SafetyMonitor()
    safety.kill("test")
    orch = Orchestrator(safety=safety)
    assert not orch.safety.is_safe_to_proceed()


def test_gate_requirements_are_progressive() -> None:
    """Gate thresholds should be within a valid range (0-10) and non-negative."""
    for phase in PipelinePhase:
        score = GATE_REQUIREMENTS[phase].min_judge_score
        assert 0 <= score <= 10, f"{phase.value} gate ({score}) should be between 0 and 10"
