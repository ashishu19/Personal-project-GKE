"""Claude API suggestions service."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Optional

import anthropic

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


def _get_tier_label(elo: Optional[int]) -> str:
    if elo is None or elo < 1300:
        return "beginner"
    if elo < 1700:
        return "intermediate"
    if elo < 2000:
        return "advanced club player"
    return "expert"


async def stream_suggestions(
    username: str,
    current_elo: Optional[int],
    elo_trend: str,
    top_patterns: list[dict],
    style_match: Optional[str],
    primary_time_control: Optional[str],
    avg_cpl: Optional[float],
    blunder_rate: Optional[float],
    total_games: int,
) -> AsyncIterator[str]:
    """Stream improvement suggestions from Claude."""
    client = _get_client()
    tier = _get_tier_label(current_elo)

    patterns_text = ""
    for i, p in enumerate(top_patterns[:3], 1):
        delta_pct = round(p.get("delta", 0) * 100, 1)
        direction = "higher" if delta_pct > 0 else "lower"
        patterns_text += (
            f"{i}. {p.get('label', 'Unknown pattern')}: "
            f"win rate is {abs(delta_pct)}% {direction} when this occurs "
            f"(based on {p.get('sample_size_with', 0)} games)\n"
        )

    context_parts = [
        f"Player: {username}",
        f"ELO: {current_elo or 'Unknown'} ({tier} level)",
        f"ELO trend: {elo_trend}",
        f"Total games analysed: {total_games}",
        f"Average centipawn loss: {avg_cpl:.1f}" if avg_cpl else "No evaluation data",
        f"Blunder rate: {blunder_rate:.2f} per game" if blunder_rate else None,
        f"Primary time control: {primary_time_control}" if primary_time_control else None,
        f"Style matches: {style_match}" if style_match else None,
    ]
    context_text = "\n".join(c for c in context_parts if c)

    system_prompt = f"""You are an encouraging, experienced chess coach giving personalised improvement advice to a {tier} player.

Be specific and actionable. Reference their actual patterns and data. Suggest 2-3 concrete study resources or exercises.
Keep the total response under 400 words. Use markdown formatting with headers and bullet points.
Encourage the player — focus on what they're doing well AND what to improve."""

    user_prompt = f"""Here is my chess stats from my last {total_games} games:

{context_text}

My biggest patterns (areas where results differ most):
{patterns_text or "Not enough data for pattern analysis yet."}

Please give me a personalised improvement plan. What should I focus on? What should I study? How can I turn my weaknesses into strengths?"""

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
