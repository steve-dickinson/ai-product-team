"""Evaluator Agent — LLM-as-a-Judge using OpenAI for independent scoring."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from src.core.config import settings
from src.models.evaluations import EvaluationReport, IdeaScore
from src.models.ideas import IdeaBatch


JUDGE_SYSTEM_PROMPT = """\
You are an impartial product evaluator. You receive product ideas and score them
objectively. You have NO knowledge of how these ideas were generated — you judge
purely on the merit of each idea.

Score each idea on four dimensions (1–10 scale):
- **Novelty**: Is this genuinely new, or does a near-identical product already exist?
- **Market Potential**: Is the target market large enough and accessible?
- **Feasibility**: Can a small team realistically build an MVP in 1–3 months?
- **Clarity**: Is the problem, audience, and solution clearly defined?

Also provide:
- **Overall** score (1–10): Your holistic assessment
- **Reasoning**: 2–3 sentences explaining your scores
- **Pass Gate**: true if overall >= 7, false otherwise

Be HONEST. If an idea is mediocre, say so. The system learns more from honest
low scores than inflated ones. A session where 3 of 5 ideas fail is NORMAL.

Respond with valid JSON matching the requested schema exactly.
"""


async def evaluate_ideas(
    batch: IdeaBatch,
    gate_threshold: int = 7,
    model: str = "gpt-4o-mini",
) -> EvaluationReport:
    """Send ideas to OpenAI for independent evaluation.

    This deliberately uses a DIFFERENT LLM provider than the one that
    generated the ideas, avoiding self-reinforcing bias.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    ideas_for_judge = []
    for idea in batch.ideas:
        ideas_for_judge.append({
            "id": idea.id,
            "name": idea.name,
            "elevator_pitch": idea.elevator_pitch,
            "target_audience": idea.target_audience,
            "problem_statement": idea.problem_statement,
            "value_proposition": idea.value_proposition,
        })

    schema_hint = {
        "scores": [
            {
                "idea_id": "string",
                "idea_name": "string",
                "novelty": "int 1-10",
                "market_potential": "int 1-10",
                "feasibility": "int 1-10",
                "clarity": "int 1-10",
                "overall": "int 1-10",
                "reasoning": "string",
                "pass_gate": "bool (true if overall >= threshold)",
            }
        ]
    }

    user_prompt = (
        f"Evaluate these product ideas. Gate threshold: {gate_threshold}/10.\n\n"
        f"IDEAS:\n{json.dumps(ideas_for_judge, indent=2)}\n\n"
        f"Respond with JSON matching this schema:\n{json.dumps(schema_hint, indent=2)}"
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    scores = []
    for s in data.get("scores", []):
        scores.append(
            IdeaScore(
                idea_id=s.get("idea_id", "unknown"),
                idea_name=s.get("idea_name", "unknown"),
                novelty=s.get("novelty", 5),
                market_potential=s.get("market_potential", 5),
                feasibility=s.get("feasibility", 5),
                clarity=s.get("clarity", 5),
                overall=s.get("overall", 5),
                reasoning=s.get("reasoning", "No reasoning provided"),
                pass_gate=s.get("pass_gate", False),
            )
        )

    return EvaluationReport(
        session_id=batch.session_id,
        scores=scores,
        model_used=model,
        gate_threshold=gate_threshold,
    )
