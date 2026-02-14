"""Loop detection — catches agents that get stuck repeating themselves."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class LoopAction(str, Enum):
    """What to do when a loop is detected."""

    INJECT_PROMPT = "inject_prompt"
    SKIP_TURN = "skip_turn"
    KILL = "kill"


@dataclass
class LoopEvent:
    """Record of a detected loop."""

    agent_name: str
    action_taken: LoopAction
    similarity_score: float
    message_window: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LoopDetector:
    """Detects repetitive agent behaviour using simple text similarity.

    The algorithm compares each new message against a sliding window
    of recent messages from the same agent. If N consecutive messages
    have similarity above the threshold, a loop is flagged.

    We use a simple word-overlap similarity (Jaccard) rather than
    embedding-based cosine similarity to avoid extra API calls.
    Jaccard is fast, free, and surprisingly effective at catching
    the verbatim or near-verbatim repetition that LLMs produce
    when stuck in a loop.
    """

    threshold: float = 0.85
    window_size: int = 3
    _history: dict[str, list[str]] = field(default_factory=dict)
    events: list[LoopEvent] = field(default_factory=list)

    def check(self, agent_name: str, message: str) -> LoopAction | None:
        """Check a new message for loop patterns.

        Returns None if no loop detected, or a LoopAction if one is.
        """
        if agent_name not in self._history:
            self._history[agent_name] = []

        history = self._history[agent_name]

        similar_count = 0
        for past_msg in history[-(self.window_size) :]:
            sim = self._jaccard_similarity(message, past_msg)
            if sim >= self.threshold:
                similar_count += 1

        history.append(message)

        if len(history) > self.window_size * 3:
            self._history[agent_name] = history[-(self.window_size * 3) :]

        if similar_count >= self.window_size - 1:
            agent_events = [e for e in self.events if e.agent_name == agent_name]

            if len(agent_events) >= 2:
                action = LoopAction.KILL
            elif len(agent_events) >= 1:
                action = LoopAction.SKIP_TURN
            else:
                action = LoopAction.INJECT_PROMPT

            event = LoopEvent(
                agent_name=agent_name,
                action_taken=action,
                similarity_score=self.threshold,
                message_window=history[-self.window_size :],
            )
            self.events.append(event)
            return action

        return None

    @staticmethod
    def _jaccard_similarity(text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts.

        Jaccard = |intersection| / |union| of word sets.
        Returns 0.0–1.0 where 1.0 = identical word sets.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)
