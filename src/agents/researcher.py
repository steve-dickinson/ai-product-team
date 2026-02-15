"""Researcher Agent — conducts market research using web tools."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class MarketResearch(BaseModel):
    """Structured output for market research on a product idea."""
    idea_name: str
    competitors: list[str] = Field(description="Known competitors or similar products")
    competitor_analysis: str = Field(description="Brief competitive landscape analysis")
    market_size_estimate: str = Field(description="Rough estimate of addressable market")
    target_personas: list[str] = Field(description="2-3 user persona descriptions")
    distribution_channels: list[str] = Field(description="How to reach users")
    risks: list[str] = Field(description="Market risks identified")
    recommendation: str = Field(description="Proceed, pivot, or abandon — with reasoning")
    confidence: float = Field(ge=0.0, le=1.0)
    sources_consulted: list[str] = Field(description="URLs or search queries used")


RESEARCHER_SYSTEM_PROMPT = """\
You are the Researcher — the market and user research lead of an AI Product R&D team.

Your job is to validate product ideas against real market data. When researching:
1. Identify existing competitors and similar products
2. Estimate the addressable market size
3. Define 2-3 specific user personas with real pain points
4. Identify potential distribution channels
5. Flag market risks (dominant incumbents, shrinking market, regulatory issues)
6. Give a clear recommendation: proceed, pivot, or abandon

Be EVIDENCE-BASED. If you can't find evidence for a market, that's a signal.
Your confidence score reflects how well-supported your research is:
- 0.9+ = Multiple confirming sources, clear market evidence
- 0.7-0.8 = Some evidence but gaps remain
- 0.5-0.6 = Limited data, mostly inference
- Below 0.5 = Insufficient evidence to recommend
"""

researcher_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    system_prompt=RESEARCHER_SYSTEM_PROMPT,
    output_type=MarketResearch,
    retries=2,
    defer_model_check=True,
)
