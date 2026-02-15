"""Stage 11: Developer agent generates a prototype, Architect reviews it.

Demonstrates:
  - Code generation from a PRD
  - Docker sandbox syntax checking
  - Structured code review
  - The generate → review → fix loop

Usage:
    uv run python stage_11.py
"""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.agents.code_reviewer import code_review_agent
from src.agents.developer import developer_agent
from src.core.config import settings
from src.core.sandbox import Sandbox

console = Console()


async def run_prototype_demo() -> None:
    if not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key:
        console.print("[red]ERROR: Set ANTHROPIC_API_KEY in .env[/red]")
        return


    prompt = (
        "Generate a Python CLI prototype for DevFocus that has 3 commands:\n"
        "- 'devfocus start 25' to start a 25 minute focus session\n"
        "- 'devfocus status' to show remaining time\n"
        "- 'devfocus stop' to stop the session\n\n"
        "Create 1-2 Python files with simple CLI implementation. Include a README."
    )

    with console.status("[green]Developer writing code..."):
        result = await developer_agent.run(prompt)

    prototype = result.output

    console.print(f"\n[bold]Prototype:[/bold] {prototype.product_name} ({prototype.id})")
    console.print(
        f"[bold]Files:[/bold] {len(prototype.files)} | "
        f"[bold]Lines:[/bold] {prototype.total_lines}"
    )
    console.print(f"[bold]Entry point:[/bold] {prototype.entry_point}")
    console.print(f"[bold]Confidence:[/bold] {prototype.confidence:.0%}\n")

    # Show each file
    for f in prototype.files:
        console.print(Panel(
            Syntax(f.content, f.language.value, theme="monokai", line_numbers=True),
            title=f"📄 {f.path}",
            subtitle=f.description,
            border_style="green",
        ))

    # ── Sandbox syntax check ──
    console.print(Panel("[bold yellow]Sandbox: Syntax Check[/bold yellow]"))

    sandbox = Sandbox()
    files_dict = {f.path: f.content for f in prototype.files}
    syntax_result = await sandbox.check_syntax(files_dict)

    if syntax_result.exit_code == 0:
        console.print("[green]✓ All files pass syntax check[/green]")
    elif "Docker not found" in syntax_result.stderr:
        console.print("[yellow]⚠ Docker not available — skipping sandbox check[/yellow]")
        console.print("[dim]  Install Docker Desktop to enable sandbox execution[/dim]")
    else:
        console.print(f"[red]✗ Syntax errors found:[/red]\n{syntax_result.stderr}")

    # ── Architect Code Review ──
    console.print(Panel("[bold yellow]Architect: Code Review[/bold yellow]"))

    review_prompt = (
        f"Review this prototype code:\n\n"
        f"Product: {prototype.product_name}\n"
        f"Prototype ID: {prototype.id}\n\n"
    )
    for f in prototype.files:
        review_prompt += f"--- {f.path} ---\n{f.content}\n\n"

    with console.status("[yellow]Architect reviewing code..."):
        review_result = await code_review_agent.run(review_prompt)

    review = review_result.output

    # Display review
    verdict_colours = {"approved": "green", "changes_requested": "yellow", "rejected": "red"}
    colour = verdict_colours.get(review.verdict.value, "white")
    console.print(f"\n[bold]Verdict:[/bold] [{colour}]{review.verdict.value.upper()}[/{colour}]")

    table = Table(title="Code Review Scores")
    table.add_column("Dimension", style="bold")
    table.add_column("Score", justify="center")
    table.add_row("Clean Code", f"{review.clean_code_score}/10")
    table.add_row("Security", f"{review.security_score}/10")
    table.add_row("Architecture", f"{review.architecture_score}/10")
    table.add_row("Overall", f"[{colour}]{review.overall_score}/10[/{colour}]")
    console.print(table)

    if review.strengths:
        console.print("\n[bold green]Strengths:[/bold green]")
        for s in review.strengths:
            console.print(f"  ✓ {s}")

    if review.issues:
        console.print("\n[bold red]Issues:[/bold red]")
        for issue in review.issues:
            console.print(f"  ✗ {issue}")

    if review.suggestions:
        console.print("\n[bold yellow]Suggestions:[/bold yellow]")
        for sug in review.suggestions:
            console.print(f"  → {sug}")


if __name__ == "__main__":
    asyncio.run(run_prototype_demo())
