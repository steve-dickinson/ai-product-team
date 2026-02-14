"""Pipeline phase definitions and gate requirements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PipelinePhase(str, Enum):
    """The seven phases of the product R&D pipeline."""

    IDEATION = "ideation"
    MARKET_RESEARCH = "market_research"
    FEASIBILITY = "feasibility"
    PRODUCT_DESIGN = "product_design"
    PROTOTYPING = "prototyping"
    TESTING = "testing"
    VIABILITY = "viability"


@dataclass(frozen=True)
class GateRequirement:
    """What must be true for an idea to pass a phase gate."""

    phase: PipelinePhase
    min_judge_score: int
    description: str

GATE_REQUIREMENTS: dict[PipelinePhase, GateRequirement] = {
    PipelinePhase.IDEATION: GateRequirement(
        PipelinePhase.IDEATION, min_judge_score=6,
        description="Novelty and clarity pass minimum bar",
    ),
    PipelinePhase.MARKET_RESEARCH: GateRequirement(
        PipelinePhase.MARKET_RESEARCH, min_judge_score=7,
        description="Market evidence supports the concept",
    ),
    PipelinePhase.FEASIBILITY: GateRequirement(
        PipelinePhase.FEASIBILITY, min_judge_score=7,
        description="Technical approach is viable and scoped",
    ),
    PipelinePhase.PRODUCT_DESIGN: GateRequirement(
        PipelinePhase.PRODUCT_DESIGN, min_judge_score=8,
        description="PRD is complete and internally consistent",
    ),
    PipelinePhase.PROTOTYPING: GateRequirement(
        PipelinePhase.PROTOTYPING, min_judge_score=7,
        description="Code passes tests and review",
    ),
    PipelinePhase.TESTING: GateRequirement(
        PipelinePhase.TESTING, min_judge_score=7,
        description="Coverage ≥ 80%, pass rate ≥ 90%",
    ),
    PipelinePhase.VIABILITY: GateRequirement(
        PipelinePhase.VIABILITY, min_judge_score=8,
        description="Final go/no-go — holistic viability",
    ),
}
