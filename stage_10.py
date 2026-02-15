"""Stage 10: PM Agent generates a full PRD from a validated idea.

This simulates Phase 4 (Product Design) of the pipeline.
The PM Agent receives a product idea + market research + feasibility
analysis and produces a comprehensive Product Requirements Document.

Usage:
    uv run python stage_10.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from src.core.config import settings
from src.agents.pm_agent import pm_agent
from src.models.prd import Priority

console = Console()


async def run_prd_generation() -> None:
    """Generate a PRD from a simulated validated idea."""

    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    # Simulated idea that has already passed ideation, research, and feasibility
    # In the real pipeline, this comes from the Orchestrator
    idea_context = """
VALIDATED PRODUCT IDEA:
  Name: DevFocus
  Pitch: A browser extension that blocks distracting websites during coding
         sessions, integrates with VS Code to detect active coding, and provides
         weekly productivity reports with commit correlation.
  Target Audience: Solo developers and small dev teams who struggle with focus
  Problem: Developers lose 2-3 hours daily to distraction but existing blockers
           are too rigid and don't understand coding workflows

MARKET RESEARCH FINDINGS:
  - Competitors: Freedom ($8/mo), Cold Turkey ($40 one-time), SelfControl (free, Mac only)
  - Gap: None integrate with IDE activity or correlate blocks with productivity
  - Market: ~30M professional developers globally, productivity tools market growing 12% YoY
  - Distribution: Chrome Web Store + VS Code Marketplace

FEASIBILITY ASSESSMENT:
  - Complexity: Medium
  - Stack: Browser extension (Chrome MV3) + VS Code extension + small backend API
  - Timeline: 6-8 weeks for MVP
  - Key risk: Chrome MV3 limitations on background processing
  - Architect confidence: 0.75
"""

    console.print(Panel("[bold blue]Phase 4: Product Design[/bold blue]\nPM Agent writing PRD..."))

    prompt = (
        f"Write a comprehensive Product Requirements Document for this validated idea.\n\n"
        f"{idea_context}\n\n"
        f"Create a detailed PRD with user stories, acceptance criteria, and MoSCoW prioritisation. "
        f"Keep the v1 scope tight — aim for 3-5 must-have features that deliver core value."
    )

    with console.status("[green]PM Agent writing PRD..."):
        result = await pm_agent.run(prompt)

    prd = result.output

    # ── Display the PRD ──
    console.print(Panel(
        f"[bold]{prd.product_name}[/bold] v{prd.version}\n"
        f"ID: {prd.id}\n"
        f"Confidence: {prd.confidence:.0%}",
        title="📋 Product Requirements Document",
        border_style="blue",
    ))

    console.print(f"\n[bold]Problem:[/bold]\n{prd.problem_statement}\n")
    console.print(f"[bold]Vision:[/bold]\n{prd.vision}\n")
    console.print(f"[bold]Target Audience:[/bold]\n{prd.target_audience}\n")

    # Scope
    console.print("[bold]In Scope (v1):[/bold]")
    for item in prd.in_scope:
        console.print(f"  ✓ {item}")
    console.print("\n[bold]Out of Scope:[/bold]")
    for item in prd.out_of_scope:
        console.print(f"  ✗ {item}")

    # Features + User Stories as a tree
    console.print()
    tree = Tree("[bold]Features & User Stories[/bold]")
    for feature in prd.features:
        priority_colours = {
            Priority.MUST: "red", Priority.SHOULD: "yellow",
            Priority.COULD: "blue", Priority.WONT: "dim",
        }
        colour = priority_colours.get(feature.priority, "white")
        branch = tree.add(f"[{colour}][{feature.priority.value}][/{colour}] [bold]{feature.name}[/bold]")
        branch.add(f"[dim]{feature.description}[/dim]")

        for us in feature.user_stories:
            us_colour = priority_colours.get(us.priority, "white")
            story = branch.add(
                f"[{us_colour}]{us.id}[/{us_colour}]: As a {us.persona}, "
                f"I want to {us.action}"
            )
            for ac in us.acceptance_criteria:
                story.add(f"[dim]AC: {ac}[/dim]")

    console.print(tree)

    # Tech details
    console.print(f"\n[bold]Suggested Stack:[/bold]\n{prd.suggested_tech_stack}")
    console.print(f"\n[bold]Data Model:[/bold]\n{prd.data_model_overview}")

    if prd.api_overview:
        console.print(f"\n[bold]API Overview:[/bold]\n{prd.api_overview}")

    # Open questions
    if prd.open_questions:
        console.print("\n[bold]Open Questions:[/bold]")
        for q in prd.open_questions:
            console.print(f"  ❓ {q}")

    # Stats
    table = Table(title="PRD Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="center")
    table.add_row("Total Features", str(len(prd.features)))
    table.add_row("Total User Stories", str(prd.total_user_stories))
    table.add_row("Must-Have Stories", str(prd.must_have_count))
    table.add_row("Open Questions", str(len(prd.open_questions)))
    table.add_row("Confidence", f"{prd.confidence:.0%}")
    console.print(table)

    # Token usage
    usage = result.usage()
    console.print(
        f"\n[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out[/dim]"
    )


if __name__ == "__main__":
    asyncio.run(run_prd_generation())
