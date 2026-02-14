"""Stage 3: Two agents debate a product idea.

The Visionary advocates, the Architect challenges.
Watch them go back and forth for 3 rounds.

Usage:
    uv run python stage_3.py
"""


from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import asyncio

from rich.console import Console
from rich.panel import Panel

from src.agents.debate_agents import architect_debate_agent, visionary_debate_agent
from src.agents.visionary import visionary_agent
from src.core.config import settings
from src.core.debate import run_debate
from src.models.debate import DebateRole

console = Console()


async def run_debate_demo() -> None:
    """Generate an idea, then debate it."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    # ── Generate one idea to debate ──
    console.print(Panel("[bold blue]Generating an idea to debate...[/bold blue]"))

    with console.status("[green]Visionary thinking..."):
        result = await visionary_agent.run("Generate innovative software product ideas.")

    idea = result.output.ideas[0]  # Take the first idea
    console.print(f"\n[bold]Debating:[/bold] {idea.name}")
    console.print(f"[dim]{idea.elevator_pitch}[/dim]\n")

    # ── Run the debate ──
    console.print(Panel("[bold yellow]Adversarial Debate — 3 Rounds[/bold yellow]"))

    outcome = await run_debate(
        idea=idea,
        advocate=visionary_debate_agent,
        critic=architect_debate_agent,
        rounds=3,
    )

    # ── Display the debate ──
    for msg in outcome.rounds:
        colour = "blue" if msg.role == DebateRole.ADVOCATE else "red"
        label = (
            "🔵 ADVOCATE (Visionary)" if msg.role == DebateRole.ADVOCATE
            else "🔴 CRITIC (Architect)"
        )

        console.print(Panel(
            msg.content,
            title=f"{label} — Round {msg.round_number}",
            subtitle=f"Confidence: {msg.confidence:.0%}",
            border_style=colour,
        ))
        console.print()

    # ── Summary ──
    consensus_icon = "🤝" if outcome.consensus_reached else "⚔️"
    console.print(Panel(
        f"{outcome.summary}\n\n"
        f"Advocate final confidence: {outcome.advocate_final_confidence:.0%}\n"
        f"Critic final confidence: {outcome.critic_final_confidence:.0%}\n"
        f"Confidence shift: {outcome.confidence_delta:+.0%}",
        title=f"{consensus_icon} Debate Outcome",
        border_style="green" if outcome.consensus_reached else "yellow",
    ))


if __name__ == "__main__":
    asyncio.run(run_debate_demo())
