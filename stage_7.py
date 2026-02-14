
"""Stage 7: Web research — Researcher validates ideas with live web data.

Usage:
    uv run python stage_7.py
"""
from __future__ import annotations
import asyncio
from rich.console import Console
from rich.panel import Panel

from src.core.config import settings
from src.agents.researcher import researcher_agent
from src.agents.visionary import visionary_agent
from src.tools.web_research import WebResearchTools

console = Console()


async def run_research_demo() -> None:
    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return

    # Generate ideas
    console.print(Panel("[bold blue]Phase 1: Ideation[/bold blue]"))
    with console.status("[green]Visionary thinking..."):
        result = await visionary_agent.run("Generate innovative software product ideas.")

    top_idea = result.output.ideas[0]
    console.print(f"[bold]Researching:[/bold] {top_idea.name}")
    console.print(f"[dim]{top_idea.elevator_pitch}[/dim]\n")

    # Web search for context
    web = WebResearchTools()
    search_context = ""
    for query in [f"{top_idea.name} competitors", f"{top_idea.target_audience} tools market"]:
        with console.status(f"[yellow]Searching: {query}[/yellow]"):
            results = await web.search_web(query)
        for r in results:
            search_context += f"- {r.title}: {r.snippet}\n"
            if r.url:
                console.print(f"  Found: [blue]{r.title}[/blue]")

    # Research with web context
    console.print(Panel("[bold blue]Phase 2: Market Research[/bold blue]"))
    prompt = (
        f"Research this product idea:\n"
        f"Name: {top_idea.name}\nPitch: {top_idea.elevator_pitch}\n"
        f"Audience: {top_idea.target_audience}\nProblem: {top_idea.problem_statement}\n\n"
        f"Web search results:\n{search_context}\n\nProvide a market research report."
    )

    with console.status("[green]Researcher analysing..."):
        research = await researcher_agent.run(prompt)

    report = research.output
    console.print(f"\n[bold]Competitors:[/bold] {', '.join(report.competitors)}")
    console.print(f"[bold]Market Size:[/bold] {report.market_size_estimate}")
    console.print(f"[bold]Recommendation:[/bold] {report.recommendation}")

    conf_colour = "green" if report.confidence >= 0.7 else "yellow"
    console.print(
        f"[bold]Confidence:[/bold] "
        f"[{conf_colour}]{report.confidence:.0%}[/{conf_colour}]"
    )


if __name__ == "__main__":
    asyncio.run(run_research_demo())
