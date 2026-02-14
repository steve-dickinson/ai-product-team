"""Stage 5: Persistent memory — Redis + MongoDB via Docker.

Demonstrates:
  - Saving agent messages to MongoDB (survives restarts)
  - Publishing messages to Redis Streams (real-time bus)
  - Replaying a session from storage

Prerequisites:
  docker compose up -d

Usage:
    uv run python stage_5.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel

from src.core.config import settings
from src.agents.visionary import visionary_agent
from src.storage.mongo_store import MongoStore
from src.storage.redis_bus import RedisBus

console = Console()


async def demo_persistent_memory() -> None:
    """Run ideation and persist everything."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    # ── Connect to infrastructure ──
    console.print(Panel("[bold blue]Stage 5: Persistent Memory[/bold blue]"))

    mongo = MongoStore()
    redis_bus = RedisBus()

    try:
        await mongo.connect()
        console.print("[green]✓ MongoDB connected[/green]")
    except Exception as e:
        console.print(f"[red]✗ MongoDB failed: {e}[/red]")
        console.print("[dim]  Run: docker compose up -d[/dim]")
        return

    try:
        await redis_bus.connect()
        console.print("[green]✓ Redis connected[/green]")
    except Exception as e:
        console.print(f"[red]✗ Redis failed: {e}[/red]")
        console.print("[dim]  Run: docker compose up -d[/dim]")
        return

    # ── Generate ideas ──
    console.print("\n[bold]Running Visionary agent...[/bold]")
    result = await visionary_agent.run("Generate innovative software product ideas.")
    batch = result.output
    usage = result.usage()

    # ── Save session to MongoDB ──
    session_id = batch.session_id
    await mongo.save_session({
        "session_id": session_id,
        "status": "running",
        "phase": "ideation",
        "ideas_count": len(batch.ideas),
    })
    console.print(f"[green]✓ Session {session_id} saved to MongoDB[/green]")

    # ── Save each idea as a message + artefact ──
    for idea in batch.ideas:
        # Save to MongoDB (permanent record)
        await mongo.save_message({
            "session_id": session_id,
            "agent": "Visionary",
            "phase": "ideation",
            "content": idea.model_dump_json(),
            "tokens_in": usage.input_tokens // len(batch.ideas),
            "tokens_out": usage.output_tokens // len(batch.ideas),
        })

        # Publish to Redis Stream (real-time)
        await redis_bus.publish_message(
            stream=f"session:{session_id}:ideation",
            agent_name="Visionary",
            content=f"Idea: {idea.name} — {idea.elevator_pitch[:100]}",
            metadata={"idea_id": idea.id, "confidence": idea.confidence},
        )

    console.print(f"[green]✓ {len(batch.ideas)} ideas saved to MongoDB + Redis[/green]")

    # ── Save cost record ──
    await mongo.save_cost_entry({
        "session_id": session_id,
        "agent": "Visionary",
        "model": "claude-sonnet-4-20250514",
        "input_tokens": usage.request_tokens,
        "output_tokens": usage.response_tokens,
        "phase": "ideation",
    })
    console.print("[green]✓ Cost entry saved[/green]")

    # ── Replay from Redis ──
    console.print("\n[bold]Replaying from Redis Stream:[/bold]")
    messages = await redis_bus.read_messages(f"session:{session_id}:ideation")
    for msg in messages:
        console.print(f"  [{msg.get('timestamp', '')}] {msg.get('agent', '')}: {msg.get('content', '')[:80]}")

    # ── Replay from MongoDB ──
    console.print("\n[bold]Replaying from MongoDB:[/bold]")
    saved = await mongo.get_session_messages(session_id)
    console.print(f"  Found {len(saved)} messages for session {session_id}")

    # ── List all sessions ──
    sessions = await mongo.get_sessions(limit=5)
    console.print(f"\n[bold]Recent sessions:[/bold] {len(sessions)} found")
    for s in sessions:
        console.print(f"  • {s.get('session_id', 'unknown')} — {s.get('phase', '')} — {s.get('status', '')}")

    # Cleanup
    await mongo.disconnect()
    await redis_bus.disconnect()
    console.print("\n[green]✓ Done! Data persists — run again and check session count grows.[/green]")


if __name__ == "__main__":
    asyncio.run(demo_persistent_memory())
