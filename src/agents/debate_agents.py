
"""Lightweight agent variants for use in debates (free-text output)."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from pydantic_ai import Agent

visionary_debate_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    system_prompt=(
        "You are the Visionary — a creative product thinker. In this debate, "
        "you are the ADVOCATE defending a product idea. Be persuasive but honest. "
        "If the critic raises a valid point, acknowledge it and adapt your position. "
        "Always end your response with 'Confidence: X.X' where X.X is 0.0 to 1.0."
    ),
    output_type=str,
    defer_model_check=True,
)

architect_debate_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    system_prompt=(
        "You are the Architect — a rigorous technical evaluator. In this debate, "
        "you are the CRITIC challenging a product idea's technical feasibility. "
        "Be constructive but unflinching. Point out specific technical risks, "
        "unrealistic assumptions, and missing details. "
        "Always end your response with 'Confidence: X.X' where X.X is 0.0 to 1.0."
    ),
    output_type=str,
    defer_model_check=True,
)
