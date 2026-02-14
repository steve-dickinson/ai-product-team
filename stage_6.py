"""Stage 6: The Orchestrator — pipeline controller with phase gates.

Demonstrates:
  - Orchestrator coordinating Visionary + Judge
  - Gate evaluation with pass/fail
  - Cost tracking across the pipeline
  - Safety monitoring throughout

Usage:
    uv run python stage_6.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import settings
from src.core.orchestrator import Orchestrator
from src.core.safety import SafetyMonitor

console = Console()


async def run_orchestrated_pipeline() -> None:
    """Run the full orchestrated ideation pipeline."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return
    if not settings.openai_api_key or "your-openai" in settings.openai_api_key:
        console.print("[red]ERROR: Set OPENAI_API_KEY in .env[/red]")
        return

    console.print(Panel(
        "[bold blue]AI Product R&D Team — Orchestrated Pipeline[/bold blue]\n"
        "Phase 1: Ideation → Judge Gate"
    ))

    # Create orchestrator with safety monitor
    safety = SafetyMonitor()
    safety.cost_tracker.budget_usd = settings.session_budget_usd
    orch = Orchestrator(safety=safety)

    # Run ideation phase
    result = await orch.execute_ideation()

    # Display results
    console.print(f"\n[bold]Phase Result: {'SUCCESS' if result.success else 'FAILED'}[/bold]")
    console.print(f"  Ideas in: {result.ideas_in}")
    console.print(f"  Ideas out: {result.ideas_out}")
    console.print(f"  Duration: {result.duration_seconds:.1f}s")

    if result.error:
        console.print(f"  [red]Error: {result.error}[/red]")

    # Show evaluation details
    if result.evaluation:
        console.print("\n[bold]Judge Scores:[/bold]")
        table = Table()
        table.add_column("Idea")
        table.add_column("Overall", justify="center")
        table.add_column("Gate", justify="center")
        table.add_column("Reasoning")

        for score in result.evaluation.scores:
            gate = "[green]PASS[/green]" if score.pass_gate else "[red]FAIL[/red]"
            table.add_row(score.idea_name, str(score.overall), gate, score.reasoning[:60] + "...")
        console.print(table)

    # Pipeline summary
    console.print(Panel(orch.summary(), title="Pipeline Summary"))


if __name__ == "__main__":
    asyncio.run(run_orchestrated_pipeline())
