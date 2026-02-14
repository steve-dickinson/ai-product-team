"""Stage 1: Run the Visionary agent and see product ideas.

Usage:
    uv run python stage_1.py
    uv run python stage_1.py "focus on developer tools"
"""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import settings
from src.agents.visionary import visionary_agent

console = Console()

async def run_visionary(focus: str = "") -> None:
    """Run the Visionary agent and display results."""

    # Check API key is set
    if not settings.anthropic_api_key or settings.anthropic_api_key == "sk-ant-your-key-here":
        console.print("[red]ERROR: Set your ANTHROPIC_API_KEY in .env[/red]")
        return

    prompt = "Generate innovative software product ideas."
    if focus:
        prompt += f" Focus area: {focus}"

    console.print(Panel(f"[bold blue]Visionary Agent — Ideation[/bold blue]\n\n{prompt}"))

    # Run the agent
    with console.status("[bold green]Visionary is thinking..."):
        result = await visionary_agent.run(prompt)

    batch = result.output

    # Display results
    console.print(f"\n[bold]Session:[/bold] {batch.session_id}")
    console.print(f"[bold]Ideas generated:[/bold] {len(batch.ideas)}\n")

    for i, idea in enumerate(batch.ideas, 1):
        # Colour the confidence badge
        conf = idea.confidence
        colour = "green" if conf >= 0.7 else "yellow" if conf >= 0.5 else "red"

        table = Table(title=f"Idea {i}: {idea.name}", show_header=False, border_style="blue")
        table.add_column(width=20)
        table.add_column()
        table.add_row("Pitch", idea.elevator_pitch)
        table.add_row("Audience", idea.target_audience)
        table.add_row("Problem", idea.problem_statement)
        table.add_row("Value Prop", idea.value_proposition)
        table.add_row("Confidence", f"[{colour}]{conf:.1%}[/{colour}]")
        console.print(table)
        console.print()

    usage = result.usage()
    console.print(
        f"[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out | "
        f"Requests: {usage.requests}[/dim]"
    )


if __name__ == "__main__":
    focus_area = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    asyncio.run(run_visionary(focus_area))
