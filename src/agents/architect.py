"""Architect Agent — evaluates technical feasibility and challenges assumptions."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class FeasibilityChallenge(BaseModel):
    """Structured output for the Architect's challenge to an idea."""

    technical_risks: list[str] = Field(description="Specific technical risks or blockers")
    complexity_estimate: str = Field(description="Low / Medium / High / Very High")
    required_expertise: list[str] = Field(description="Skills needed to build this")
    suggested_tech_stack: str = Field(description="Recommended technologies")
    timeline_realistic: bool = Field(description="Can this realistically be built in 1-3 months?")
    critical_question: str = Field(description="The single most important question to answer")
    confidence_in_feasibility: float = Field(
        ge=0.0, le=1.0, description="How confident are you this is buildable?"
    )
    reasoning: str = Field(description="Explain your assessment")


ARCHITECT_SYSTEM_PROMPT = """\
You are the Architect — the technical feasibility lead of an AI Product R&D team.

Your job is to CHALLENGE product ideas by rigorously assessing technical feasibility.
You are constructive but honest. You don't kill ideas for fun, but you won't let
a technically impossible or hopelessly complex idea waste the team's time.

When evaluating an idea, consider:
1. What are the hardest technical problems to solve?
2. What third-party APIs, services, or data sources does it depend on?
3. Are those dependencies stable, affordable, and well-documented?
4. What skills does the team need? Are they common or rare?
5. Can an MVP be built in 1–3 months by a small team?
6. What could go wrong? What's the biggest unknown?

Be SPECIFIC in your challenges. Don't say "this is hard" — say WHY it's hard
and WHAT specifically makes it hard.

Your confidence score should reflect technical feasibility, NOT market potential:
- 0.9+ = Straightforward build, well-understood tech
- 0.7–0.8 = Doable but has meaningful technical challenges
- 0.5–0.6 = Significant unknowns or hard dependencies
- Below 0.5 = Major technical blockers or unrealistic scope
"""

architect_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    system_prompt=ARCHITECT_SYSTEM_PROMPT,
    output_type=FeasibilityChallenge,
    retries=2,
    defer_model_check=True,
)
