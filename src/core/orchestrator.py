"""Orchestrator — the pipeline controller that coordinates all agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from rich.console import Console

from src.agents.evaluator import evaluate_ideas
from src.agents.visionary import visionary_agent
from src.core.cost_tracker import BudgetExceededError
from src.core.phases import GATE_REQUIREMENTS, PipelinePhase
from src.core.safety import SafetyMonitor, SystemStatus
from src.models.evaluations import EvaluationReport
from src.models.ideas import IdeaBatch, IdeaStatus

console = Console()


@dataclass
class PhaseResult:
    """The outcome of running a single pipeline phase."""

    phase: PipelinePhase
    success: bool
    ideas_in: int
    ideas_out: int
    evaluation: EvaluationReport | None = None
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass
class PipelineRun:
    """State for a complete pipeline execution."""

    session_id: str = ""
    current_phase: PipelinePhase = PipelinePhase.IDEATION
    phase_results: list[PhaseResult] = field(default_factory=list)
    active_ideas: list[Any] = field(default_factory=list)
    archived_ideas: list[Any] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Orchestrator:
    """Pipeline controller — manages agents, phases, gates, and safety.

    The Orchestrator is the central authority. It:
      - Decides which agents run in which order
      - Enforces quality gates between phases
      - Tracks costs and checks budget before every action
      - Monitors for loops and other safety issues
      - Archives failed ideas with reasons
    """

    def __init__(self, safety: SafetyMonitor | None = None) -> None:
        self.safety = safety or SafetyMonitor()
        self.run: PipelineRun = PipelineRun()

    async def execute_ideation(self, focus: str = "") -> PhaseResult:
        """Execute Phase 1: Ideation.

        The Visionary generates ideas, the Judge evaluates them,
        and ideas below the gate threshold are archived.
        """
        phase = PipelinePhase.IDEATION
        start = datetime.now(timezone.utc)

        console.print(f"\n[bold blue]═══ Phase: {phase.value.upper()} ═══[/bold blue]")

        if not self.safety.is_safe_to_proceed():
            return PhaseResult(phase=phase, success=False, ideas_in=0, ideas_out=0,
                               error=f"System status: {self.safety.status.value}")

        try:
            console.print("[dim]Visionary generating ideas...[/dim]")
            prompt = "Generate innovative software product ideas."
            if focus:
                prompt += f" Focus area: {focus}"

            result = await visionary_agent.run(prompt)
            batch = result.output
            usage = result.usage()

            self.run.session_id = batch.session_id

            self.safety.record_cost(
                agent_name="Visionary",
                model="claude-sonnet-4-20250514",
                input_tokens=usage.request_tokens,
                output_tokens=usage.response_tokens,
                phase=phase.value,
            )

            for idea in batch.ideas:
                self.safety.check_agent_message("Visionary", idea.elevator_pitch)

            console.print(f"[green]✓ Generated {len(batch.ideas)} ideas[/green]")

            console.print("[dim]Judge evaluating...[/dim]")
            gate = GATE_REQUIREMENTS[phase]
            evaluation = await evaluate_ideas(batch, gate_threshold=gate.min_judge_score)

            passed_ideas = []
            for idea in batch.ideas:
                score = next(
                    (s for s in evaluation.scores if s.idea_id == idea.id or s.idea_name == idea.name),
                    None,
                )
                if score and score.pass_gate:
                    idea.status = IdeaStatus.PASSED
                    passed_ideas.append(idea)
                    console.print(f"  [green]✓ {idea.name} — PASSED (score: {score.overall})[/green]")
                else:
                    idea.status = IdeaStatus.FAILED
                    self.run.archived_ideas.append(idea)
                    fail_score = score.overall if score else "N/A"
                    console.print(f"  [red]✗ {idea.name} — FAILED (score: {fail_score})[/red]")

            self.run.active_ideas = passed_ideas
            self.run.current_phase = phase

            duration = (datetime.now(timezone.utc) - start).total_seconds()

            return PhaseResult(
                phase=phase,
                success=len(passed_ideas) > 0,
                ideas_in=len(batch.ideas),
                ideas_out=len(passed_ideas),
                evaluation=evaluation,
                duration_seconds=duration,
            )

        except BudgetExceededError as e:
            return PhaseResult(phase=phase, success=False, ideas_in=0, ideas_out=0, error=str(e))
        except Exception as e:
            return PhaseResult(phase=phase, success=False, ideas_in=0, ideas_out=0, error=str(e))

    def summary(self) -> str:
        """Summarise the current pipeline state."""
        lines = [
            f"Session: {self.run.session_id}",
            f"Phase: {self.run.current_phase.value}",
            f"Active ideas: {len(self.run.active_ideas)}",
            f"Archived ideas: {len(self.run.archived_ideas)}",
            f"System status: {self.safety.status.value}",
            f"Cost: {self.safety.cost_tracker.summary()}",
        ]
        return "\n".join(lines)
