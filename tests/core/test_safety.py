"""Tests for safety systems."""

from __future__ import annotations

import pytest

from src.core.cost_tracker import BudgetExceededError, CostTracker
from src.core.loop_detector import LoopAction, LoopDetector
from src.core.safety import SafetyMonitor, SystemStatus


class TestCostTracker:
    def test_records_cost(self) -> None:
        tracker = CostTracker(budget_usd=10.0)
        entry = tracker.record("agent1", "gpt-4o-mini", 1000, 500)
        assert entry.cost_usd > 0
        assert tracker.total_cost > 0

    def test_budget_exceeded_raises(self) -> None:
        tracker = CostTracker(budget_usd=0.001)  # Tiny budget
        with pytest.raises(BudgetExceededError):
            tracker.record("agent1", "claude-opus-4-20250514", 100_000, 100_000)

    def test_cost_by_agent(self) -> None:
        tracker = CostTracker(budget_usd=100.0)
        tracker.record("agent1", "gpt-4o-mini", 1000, 500)
        tracker.record("agent2", "gpt-4o-mini", 2000, 1000)
        by_agent = tracker.cost_by_agent()
        assert "agent1" in by_agent
        assert "agent2" in by_agent


class TestLoopDetector:
    def test_no_loop_on_varied_messages(self) -> None:
        detector = LoopDetector()
        assert detector.check("agent", "Hello world") is None
        assert detector.check("agent", "How are you doing today") is None
        assert detector.check("agent", "The weather is nice") is None

    def test_detects_loop_on_repeated_messages(self) -> None:
        detector = LoopDetector(window_size=3, threshold=0.85)
        msg = "I think we should build an AI assistant for productivity"
        detector.check("agent", msg)
        detector.check("agent", msg)
        result = detector.check("agent", msg)
        assert result is not None

    def test_escalates_across_detections(self) -> None:
        detector = LoopDetector(window_size=2, threshold=0.80)
        msg = "Repeated message about the same topic over and over"
        # First loop
        detector.check("agent", msg)
        first = detector.check("agent", msg)
        assert first == LoopAction.INJECT_PROMPT

        # Second loop
        detector.check("agent", msg)
        second = detector.check("agent", msg)
        assert second == LoopAction.KILL


class TestSafetyMonitor:
    def test_pause_and_resume(self) -> None:
        monitor = SafetyMonitor()
        assert monitor.is_safe_to_proceed()
        monitor.pause()
        assert not monitor.is_safe_to_proceed()
        monitor.resume()
        assert monitor.is_safe_to_proceed()

    def test_kill_switch(self) -> None:
        monitor = SafetyMonitor()
        monitor.kill("test kill")
        assert monitor.status == SystemStatus.KILLED
        assert not monitor.is_safe_to_proceed()
