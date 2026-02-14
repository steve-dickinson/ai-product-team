"""Debate engine — manages structured back-and-forth between two agents."""

from __future__ import annotations

from pydantic_ai import Agent

from src.models.debate import DebateMessage, DebateOutcome, DebateRole
from src.models.ideas import ProductIdea


async def run_debate(
    idea: ProductIdea,
    advocate: Agent[None, None],
    critic: Agent[None, None],
    rounds: int = 3,
) -> DebateOutcome:
    """Run a structured debate between two agents about a product idea.

    The debate follows this pattern:
      Round 1: Advocate presents the case → Critic challenges
      Round 2: Advocate responds to challenges → Critic rebuts
      Round 3: Advocate makes final case → Critic gives final assessment

    Args:
        idea: The product idea being debated.
        advocate: The agent defending the idea (typically Visionary).
        critic: The agent challenging it (typically Architect).
        rounds: Number of debate rounds (default 3).

    Returns:
        A DebateOutcome with the full transcript and result.
    """
    messages: list[DebateMessage] = []
    conversation_context = f"Product idea under debate: {idea.name}\n{idea.elevator_pitch}\n"

    advocate_confidence = idea.confidence
    critic_confidence = 0.5

    for round_num in range(1, rounds + 1):
        if round_num == 1:
            advocate_prompt = (
                f"{conversation_context}\n"
                f"You are the ADVOCATE. Make the strongest case for why this product idea "
                f"is worth building. Address: the problem is real, the market exists, and "
                f"this can be built. Be specific and persuasive.\n"
                f"End with your confidence (0.0–1.0) that this idea should proceed."
            )
        else:
            last_critic = messages[-1]
            advocate_prompt = (
                f"{conversation_context}\n"
                f"The critic's challenge (round {round_num - 1}):\n"
                f'"{last_critic.content}"\n\n'
                f"Respond to these specific challenges. Acknowledge valid points, "
                f"counter weak ones, and adjust your position if warranted.\n"
                f"End with your updated confidence (0.0–1.0)."
            )

        advocate_result = await advocate.run(advocate_prompt)
        advocate_text = str(advocate_result.output)

        advocate_confidence = _extract_confidence(advocate_text, advocate_confidence)

        messages.append(DebateMessage(
            agent_name="Visionary",
            role=DebateRole.ADVOCATE,
            content=advocate_text,
            round_number=round_num,
            confidence=advocate_confidence,
        ))

        critic_prompt = (
            f"{conversation_context}\n"
            f"Debate history so far:\n"
        )
        for msg in messages:
            critic_prompt += f"\n[{msg.agent_name} - Round {msg.round_number}]:\n{msg.content}\n"

        if round_num == rounds:
            critic_prompt += (
                f"\nThis is the FINAL round. Give your definitive technical assessment. "
                f"Summarise the key risks, acknowledge strengths, and state your final "
                f"confidence (0.0–1.0) that this idea is technically feasible."
            )
        else:
            critic_prompt += (
                f"\nYou are the CRITIC. Challenge the advocate's claims with SPECIFIC "
                f"technical concerns. Ask pointed questions. Identify assumptions.\n"
                f"End with your confidence (0.0–1.0) that this is technically feasible."
            )

        critic_result = await critic.run(critic_prompt)
        critic_text = str(critic_result.output)

        critic_confidence = _extract_confidence(critic_text, critic_confidence)

        messages.append(DebateMessage(
            agent_name="Architect",
            role=DebateRole.CRITIC,
            content=critic_text,
            round_number=round_num,
            confidence=critic_confidence,
        ))

    consensus = abs(advocate_confidence - critic_confidence) < 0.2

    return DebateOutcome(
        idea_name=idea.name,
        rounds=messages,
        advocate_final_confidence=advocate_confidence,
        critic_final_confidence=critic_confidence,
        consensus_reached=consensus,
        summary=(
            f"After {rounds} rounds, the Advocate's confidence is {advocate_confidence:.0%} "
            f"and the Critic's is {critic_confidence:.0%}. "
            f"{'Consensus reached.' if consensus else 'No consensus — significant disagreement remains.'}"
        ),
    )


def _extract_confidence(text: str, fallback: float) -> float:
    """Try to extract a confidence value from agent text.

    Looks for patterns like 'confidence: 0.7' or 'Confidence: 0.85'
    in the last portion of the text.
    """
    import re

    patterns = [
        r"confidence[:\s]+(\d+\.?\d*)",
        r"(\d+\.?\d*)\s*/\s*1\.0",
        r"(\d+\.?\d*)\s*confidence",
    ]

    tail = text[-200:].lower()
    for pattern in patterns:
        match = re.search(pattern, tail)
        if match:
            val = float(match.group(1))
            if 0.0 <= val <= 1.0:
                return val
            if 1.0 < val <= 10.0:
                return val / 10.0

    return fallback
