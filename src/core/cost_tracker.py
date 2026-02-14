"""Real-time cost tracking for LLM API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-3-5-20241022": (0.80, 4.00),
    "claude-opus-4-20250514": (15.00, 75.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


@dataclass
class CostEntry:
    """A single API call's cost record."""

    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    phase: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CostTracker:
    """Tracks cumulative costs across all agents and phases.

    Thread-safe for single-threaded async — if you need true
    thread safety, wrap mutations in a lock.
    """

    budget_usd: float = 15.0
    entries: list[CostEntry] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        """Total spend so far."""
        return sum(e.cost_usd for e in self.entries)

    @property
    def remaining_budget(self) -> float:
        """How much budget is left."""
        return max(0.0, self.budget_usd - self.total_cost)

    @property
    def is_over_budget(self) -> bool:
        """Have we exceeded the budget?"""
        return self.total_cost >= self.budget_usd

    def record(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        phase: str = "",
    ) -> CostEntry:
        """Record a new API call and return the cost entry.

        Raises BudgetExceededError if this call pushes us over budget.
        """
        pricing = MODEL_PRICING.get(model, (5.0, 15.0))
        cost = (input_tokens * pricing[0] + output_tokens * pricing[1]) / 1_000_000

        entry = CostEntry(
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            phase=phase,
        )
        self.entries.append(entry)

        if self.is_over_budget:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_cost:.4f} / ${self.budget_usd:.2f}"
            )

        return entry

    def cost_by_agent(self) -> dict[str, float]:
        """Get total cost broken down by agent."""
        costs: dict[str, float] = {}
        for entry in self.entries:
            costs[entry.agent_name] = costs.get(entry.agent_name, 0.0) + entry.cost_usd
        return costs

    def cost_by_phase(self) -> dict[str, float]:
        """Get total cost broken down by phase."""
        costs: dict[str, float] = {}
        for entry in self.entries:
            key = entry.phase or "unassigned"
            costs[key] = costs.get(key, 0.0) + entry.cost_usd
        return costs

    def summary(self) -> str:
        """Human-readable cost summary."""
        lines = [
            f"Total: ${self.total_cost:.4f} / ${self.budget_usd:.2f} "
            f"({self.total_cost / self.budget_usd * 100:.1f}%)",
            f"Remaining: ${self.remaining_budget:.4f}",
            f"API calls: {len(self.entries)}",
        ]
        for agent, cost in sorted(self.cost_by_agent().items()):
            lines.append(f"  {agent}: ${cost:.4f}")
        return "\n".join(lines)


class BudgetExceededError(Exception):
    """Raised when spending exceeds the configured budget."""
