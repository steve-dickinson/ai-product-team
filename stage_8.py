"""Stage 8: Learning & Fail-Fast — institutional memory.

Demonstrates:
  - Archiving failed concepts to the graveyard
  - Extracting lessons from failures
  - Building context for future sessions from past learning
  - Failure trend analysis

Usage:
    uv run python stage_8.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.agents.evaluator import evaluate_ideas
from src.agents.visionary import visionary_agent
from src.core.config import settings
from src.core.learning_engine import LearningEngine
from src.models.learning import (
    FailureReason,
    Lesson,
    LessonCategory,
)

console = Console()


async def run_learning_demo() -> None:
    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    engine = LearningEngine()

    # ── Simulate prior sessions' lessons (in real use, loaded from MongoDB) ──
    console.print(Panel("[bold blue]Loading institutional memory...[/bold blue]"))

    prior_lessons = [
        Lesson(
            session_id="session_001",
            agent_name="Researcher",
            phase="ideation",
            category=LessonCategory.MARKET_INSIGHT,
            observation=(
                "AI-powered writing tools have extreme competition — avoid unless targeting a "
                "specific niche"
            ),
            evidence="3 of 4 writing-tool ideas failed market research in sessions 1-3",
            confidence=0.85,
        ),
        Lesson(
            session_id="session_003",
            agent_name="Architect",
            phase="feasibility",
            category=LessonCategory.TECHNICAL_DISCOVERY,
            observation=(
                "Browser extensions have significantly faster time-to-market than SaaS platforms"
            ),
            evidence="Extension prototype built in 2 hours vs 2 weeks for SaaS MVP",
            confidence=0.9,
        ),
        Lesson(
            session_id="session_005",
            agent_name="Visionary",
            phase="ideation",
            category=LessonCategory.STRATEGIC_PIVOT,
            observation=(
                "Developer tools targeting solo freelancers convert better with usage-based pricing"
            ),
            evidence="Freelancer personas rejected flat-rate pricing in simulated user tests",
            confidence=0.7,
        ),
    ]

    for lesson in prior_lessons:
        engine.record_lesson(lesson)
    console.print(f"  Loaded {len(prior_lessons)} lessons from prior sessions")

    # Simulate graveyard entries
    from src.models.ideas import ProductIdea
    failed_ideas = [
        (
            "AI Email Writer Pro",
            "market_saturated",
            "ideation",
            "14 direct competitors with >100K users each",
        ),
        (
            "Universal API Monitor",
            "technical_blocker",
            "feasibility",
            "Requires kernel-level access on all major OS",
        ),
    ]
    for name, reason, phase, detail in failed_ideas:
        idea = ProductIdea(
            name=name, elevator_pitch="Test", target_audience="Test",
            value_proposition="Test", problem_statement="Test", confidence=0.5,
        )
        engine.archive_concept(
            idea=idea, session_id="session_prior", failure_phase=phase,
            failure_reason=FailureReason(reason), failure_detail=detail,
        )
    console.print(f"  Loaded {len(failed_ideas)} graveyard entries")

    # ── Build context for this session ──
    context = engine.build_context_for_session(phase="ideation")
    console.print(Panel(context, title="Context Injected Into Agent Prompts"))

    # ── Run ideation WITH learning context ──
    console.print(Panel("[bold blue]Ideation (with institutional memory)[/bold blue]"))

    enhanced_prompt = (
        f"Generate innovative software product ideas.\n\n"
        f"INSTITUTIONAL KNOWLEDGE FROM PRIOR SESSIONS:\n{context}\n\n"
        f"Use these lessons to avoid known pitfalls and focus on higher-probability areas."
    )

    with console.status("[green]Visionary thinking (informed by past sessions)..."):
        result = await visionary_agent.run(enhanced_prompt)

    batch = result.output

    for idea in batch.ideas:
        console.print(f"  • [bold]{idea.name}[/bold] (confidence: {idea.confidence:.0%})")

    # ── Evaluate and handle failures ──
    if settings.openai_api_key and "your-openai" not in settings.openai_api_key:
        console.print("\n[dim]Judge evaluating...[/dim]")
        report = await evaluate_ideas(batch, gate_threshold=6)

        for idea, score in zip(batch.ideas, report.scores, strict=True):
            if not score.pass_gate:
                # Archive to graveyard with analysis
                entry = engine.archive_concept(
                    idea=idea,
                    session_id=batch.session_id,
                    failure_phase="ideation",
                    failure_reason=FailureReason.LOW_NOVELTY if score.novelty < 6
                        else FailureReason.UNCLEAR_VALUE_PROP,
                    failure_detail=score.reasoning,
                    judge_score=score.overall,
                    resurrection_conditions=(
                        "Revisit if competitive landscape changes significantly"
                    ),
                )

                # Extract a lesson
                lesson = Lesson(
                    session_id=batch.session_id,
                    agent_name="Evaluator",
                    phase="ideation",
                    category=LessonCategory.ANTI_PATTERN,
                    observation=f"Ideas similar to '{idea.name}' score low on "
                                f"{'novelty' if score.novelty < 6 else 'clarity'}",
                    evidence=score.reasoning,
                    confidence=0.6,
                )
                engine.record_lesson(lesson)

                console.print(
                    f"  [red]✗ {idea.name} → graveyard ({entry.failure_reason.value})[/red]"
                )
            else:
                console.print(f"  [green]✓ {idea.name} — passed[/green]")

    # ── Show learning state ──
    console.print(Panel(engine.session_learning_summary(), title="Institutional Memory Status"))

    # ── Show failure trends ──
    trends = engine.get_failure_trends()
    if trends:
        console.print("\n[bold]Failure Trend Analysis:[/bold]")
        table = Table()
        table.add_column("Pattern")
        table.add_column("Count", justify="center")
        for pattern, count in trends.items():
            table.add_row(pattern, str(count))
        console.print(table)

    # ── Show graveyard ──
    console.print(f"\n[bold]Concept Graveyard:[/bold] {len(engine.graveyard)} entries")
    for entry in engine.graveyard[-5:]:
        console.print(
            f"  💀 {entry.concept_name} — {entry.failure_reason.value} "
            f"at {entry.failure_phase} (score: {entry.judge_score})"
        )


if __name__ == "__main__":
    asyncio.run(run_learning_demo())
