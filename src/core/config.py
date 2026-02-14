"""Centralised configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

@dataclass(frozen=True)
class Settings:
    """Application settings — immutable after creation."""

    anthropic_api_key: str
    openai_api_key: str
    session_budget_usd: float
    max_turns_per_phase: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            session_budget_usd=float(os.environ.get("SESSION_BUDGET_USD", "15.0")),
            max_turns_per_phase=int(os.environ.get("MAX_TURNS_PER_PHASE", "20")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )

settings = Settings.from_env()
