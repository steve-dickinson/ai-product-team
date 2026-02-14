"""Stage 2: Visionary generates ideas, Judge evaluates them.

This demonstrates the dual-LLM architecture:
  Claude (Visionary) → generates ideas
  GPT (Judge)        → scores them independently

Usage:
    uv run python stage_2.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import settings
from src.agents.evaluator import evaluate_ideas
from src.agents.visionary import visionary_agent

console = Console()


async def run_ideation_with_evaluation() -> None:
    """Full ideation → evaluation pipeline."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return
    if not settings.openai_api_key or "your-openai" in settings.openai_api_key:
        console.print("[red]ERROR: Set OPENAI_API_KEY in .env[/red]")
        return

    # ── Phase 1: Ideation ──
    console.print(Panel("[bold blue]Phase 1: Ideation[/bold blue]\nVisionary (Claude) generating ideas..."))

    with console.status("[bold green]Visionary is thinking..."):
        result = await visionary_agent.run("Generate innovative software product ideas.")

    batch = result.output
    console.print(f"[green]✓ Generated {len(batch.ideas)} ideas[/green]\n")

    for idea in batch.ideas:
        console.print(f"  • [bold]{idea.name}[/bold] (confidence: {idea.confidence:.0%})")
    console.print()

    # ── Judge Evaluation ──
    console.print(Panel("[bold yellow]Judge Evaluation[/bold yellow]\nEvaluator (GPT) scoring ideas independently..."))

    with console.status("[bold yellow]Judge is evaluating..."):
        report = await evaluate_ideas(batch)

    # ── Results ──
    console.print(Panel("[bold green]Results — Gate Threshold: 7/10[/bold green]"))

    table = Table()
    table.add_column("Idea", style="bold")
    table.add_column("Novel", justify="center")
    table.add_column("Market", justify="center")
    table.add_column("Feasib", justify="center")
    table.add_column("Clarity", justify="center")
    table.add_column("Overall", justify="center")
    table.add_column("Gate", justify="center")

    passed = 0
    for score in report.scores:
        gate_str = "[green]✓ PASS[/green]" if score.pass_gate else "[red]✗ FAIL[/red]"
        if score.pass_gate:
            passed += 1

        overall_colour = "green" if score.overall >= 7 else "yellow" if score.overall >= 5 else "red"

        table.add_row(
            score.idea_name,
            str(score.novelty),
            str(score.market_potential),
            str(score.feasibility),
            str(score.clarity),
            f"[{overall_colour}]{score.overall}[/{overall_colour}]",
            gate_str,
        )

    console.print(table)
    console.print(f"\n[bold]{passed}/{len(report.scores)} ideas passed the gate[/bold]")

    # Show reasoning for each
    console.print("\n[bold]Judge's Reasoning:[/bold]")
    for score in report.scores:
        icon = "✓" if score.pass_gate else "✗"
        console.print(f"\n  {icon} [bold]{score.idea_name}[/bold]")
        console.print(f"    {score.reasoning}")


if __name__ == "__main__":
    asyncio.run(run_ideation_with_evaluation())
