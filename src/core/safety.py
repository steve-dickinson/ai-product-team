"""Safety monitor — combines cost tracking, loop detection, and kill switch."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.core.cost_tracker import BudgetExceededError, CostTracker
from src.core.loop_detector import LoopAction, LoopDetector


class SystemStatus(str, Enum):
    """Overall system status."""

    RUNNING = "running"
    PAUSED = "paused"
    KILLED = "killed"
    COMPLETED = "completed"


@dataclass
class SafetyEvent:
    """Record of any safety-related event."""

    event_type: str
    agent_name: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SafetyMonitor:
    """Central safety authority for the pipeline.

    Combines cost tracking, loop detection, pause/resume, and kill switch
    into a single monitor that the Orchestrator checks before every action.
    """

    cost_tracker: CostTracker = field(default_factory=lambda: CostTracker())
    loop_detector: LoopDetector = field(default_factory=lambda: LoopDetector())
    status: SystemStatus = SystemStatus.RUNNING
    events: list[SafetyEvent] = field(default_factory=list)

    def is_safe_to_proceed(self) -> bool:
        """Check if the system is in a state where agents can act."""
        return self.status == SystemStatus.RUNNING

    def check_agent_message(self, agent_name: str, message: str) -> LoopAction | None:
        """Check an agent's message for safety issues.

        Returns None if safe, or a LoopAction if a loop is detected.
        """
        if not self.is_safe_to_proceed():
            return LoopAction.KILL

        loop_action = self.loop_detector.check(agent_name, message)
        if loop_action:
            self.events.append(SafetyEvent(
                event_type=f"loop_detected:{loop_action.value}",
                agent_name=agent_name,
                message=f"Loop detected — action: {loop_action.value}",
            ))
            if loop_action == LoopAction.KILL:
                self.kill("Loop escalation — agent stuck in infinite loop")
        return loop_action

    def record_cost(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        phase: str = "",
    ) -> None:
        """Record an API call's cost. Triggers kill if over budget."""
        try:
            self.cost_tracker.record(
                agent_name=agent_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                phase=phase,
            )
        except BudgetExceededError as e:
            self.events.append(SafetyEvent(
                event_type="budget_exceeded",
                agent_name=agent_name,
                message=str(e),
            ))
            self.kill(str(e))
            raise

    def pause(self) -> None:
        """Pause the pipeline — agents will stop at the next check."""
        if self.status == SystemStatus.RUNNING:
            self.status = SystemStatus.PAUSED
            self.events.append(SafetyEvent(
                event_type="paused",
                agent_name="system",
                message="Pipeline paused by operator",
            ))

    def resume(self) -> None:
        """Resume a paused pipeline."""
        if self.status == SystemStatus.PAUSED:
            self.status = SystemStatus.RUNNING
            self.events.append(SafetyEvent(
                event_type="resumed",
                agent_name="system",
                message="Pipeline resumed by operator",
            ))

    def kill(self, reason: str = "Manual kill") -> None:
        """Emergency stop — immediately halt everything."""
        self.status = SystemStatus.KILLED
        self.events.append(SafetyEvent(
            event_type="killed",
            agent_name="system",
            message=f"KILL SWITCH: {reason}",
        ))
