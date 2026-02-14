"""Stage 4: Safety rails — loop detection, cost tracking, kill switch.

Demonstrates:
  - Cost tracking across multiple agent calls
  - Loop detection catching repetitive output
  - Kill switch triggering on budget or loop escalation

Usage:
    uv run python stage_4.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import settings
from src.agents.visionary import visionary_agent
from src.core.safety import SafetyMonitor, SystemStatus

console = Console()


async def demo_safety_rails() -> None:
    """Demonstrate the safety systems."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    # Create a safety monitor with a tight budget for demo purposes
    monitor = SafetyMonitor()
    monitor.cost_tracker.budget_usd = 2.0  # Low budget for demo

    console.print(Panel("[bold blue]Safety Rails Demo[/bold blue]"))

    # ── Demo 1: Cost tracking ──
    console.print("\n[bold]Demo 1: Cost Tracking[/bold]")

    result = await visionary_agent.run("Generate innovative software product ideas.")
    usage = result.usage()

    monitor.record_cost(
        agent_name="Visionary",
        model="claude-sonnet-4-20250514",
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        phase="ideation",
    )

    console.print(f"  [green]✓ Recorded cost for Visionary[/green]")
    console.print(f"  {monitor.cost_tracker.summary()}")

    # ── Demo 2: Loop detection ──
    console.print("\n[bold]Demo 2: Loop Detection[/bold]")

    # Simulate an agent stuck in a loop
    repeated_msg = "I think we should build an AI assistant that helps with tasks."
    for i in range(4):
        action = monitor.check_agent_message("StuckAgent", repeated_msg)
        if action:
            console.print(f"  [red]⚠ Loop detected on message {i + 1}! Action: {action.value}[/red]")
        else:
            console.print(f"  [green]✓ Message {i + 1}: OK[/green]")

    # ── Demo 3: Pause / Resume ──
    console.print("\n[bold]Demo 3: Pause / Resume[/bold]")

    monitor = SafetyMonitor()  # Fresh monitor
    console.print(f"  Status: {monitor.status.value}")

    monitor.pause()
    console.print(f"  After pause: {monitor.status.value}")
    console.print(f"  Safe to proceed: {monitor.is_safe_to_proceed()}")

    monitor.resume()
    console.print(f"  After resume: {monitor.status.value}")
    console.print(f"  Safe to proceed: {monitor.is_safe_to_proceed()}")

    # ── Demo 4: Kill switch ──
    console.print("\n[bold]Demo 4: Kill Switch[/bold]")

    monitor.kill("Demo kill — testing emergency stop")
    console.print(f"  Status: {monitor.status.value}")
    console.print(f"  Safe to proceed: {monitor.is_safe_to_proceed()}")

    # ── Event log ──
    console.print("\n[bold]Safety Event Log:[/bold]")
    table = Table()
    table.add_column("Time", style="dim")
    table.add_column("Type")
    table.add_column("Agent")
    table.add_column("Message")

    for event in monitor.events:
        table.add_row(
            event.timestamp.strftime("%H:%M:%S"),
            event.event_type,
            event.agent_name,
            event.message,
        )
    console.print(table)


if __name__ == "__main__":
    asyncio.run(demo_safety_rails())
