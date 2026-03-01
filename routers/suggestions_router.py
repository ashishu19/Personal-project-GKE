"""POST /api/suggestions — streaming Claude improvement suggestions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Game, get_session
from models.schemas import SuggestionsRequest
from services.llm import stream_suggestions
from services.pattern_stats import compute_patterns

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


@router.post("")
async def get_suggestions(
    body: SuggestionsRequest,
    session: AsyncSession = Depends(get_session),
):
    username = body.username

    # Gather context from DB
    result = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.avg(Game.avg_cpl).label("avg_cpl"),
            func.avg(Game.blunders).label("avg_blunders"),
        ).where(Game.username == username)
    )
    row = result.one()
    total = row.total or 0
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No games found for '{username}'")

    avg_cpl = float(row.avg_cpl) if row.avg_cpl else None
    blunder_rate = float(row.avg_blunders) if row.avg_blunders else None

    # Most recent ELO
    elo_result = await session.execute(
        select(Game.user_elo)
        .where(Game.username == username, Game.user_elo != None)  # noqa: E711
        .order_by(desc(Game.played_at))
        .limit(1)
    )
    current_elo = elo_result.scalar_one_or_none()

    # ELO trend: compare first vs last 10 games
    first_elo_r = await session.execute(
        select(Game.user_elo)
        .where(Game.username == username, Game.user_elo != None)  # noqa: E711
        .order_by(Game.played_at.asc())
        .limit(1)
    )
    first_elo = first_elo_r.scalar_one_or_none()
    if current_elo and first_elo and current_elo != first_elo:
        diff = current_elo - first_elo
        elo_trend = f"{'+' if diff > 0 else ''}{diff} across {total} analysed games"
    else:
        elo_trend = "stable"

    # Most common time control
    tc_result = await session.execute(
        select(Game.time_control, func.count(Game.id).label("cnt"))
        .where(Game.username == username, Game.time_control != None)  # noqa: E711
        .group_by(Game.time_control)
        .order_by(desc("cnt"))
        .limit(1)
    )
    tc_row = tc_result.one_or_none()
    primary_tc = tc_row.time_control if tc_row else None

    # Top patterns
    patterns = await compute_patterns(session, username, current_elo)
    significant_patterns = [p for p in patterns if p.is_significant][:3]
    top_patterns_dicts = [
        {
            "label": p.label,
            "delta": p.delta,
            "win_rate_with": p.win_rate_with,
            "sample_size_with": p.sample_size_with,
        }
        for p in significant_patterns
    ]

    # Style match (optional)
    from services.style_matcher import compute_style_match
    style = await compute_style_match(session, username)
    style_match_str = f"{style.matched_gm} ({style.archetype})" if style else None

    async def generate():
        try:
            async for chunk in stream_suggestions(
                username=username,
                current_elo=current_elo,
                elo_trend=elo_trend,
                top_patterns=top_patterns_dicts,
                style_match=style_match_str,
                primary_time_control=primary_tc,
                avg_cpl=avg_cpl,
                blunder_rate=blunder_rate,
                total_games=total,
            ):
                yield chunk
        except RuntimeError as e:
            yield f"\n\n[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")
