"""GET /api/stats/overview|patterns|openings|style"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Game, get_session
from models.schemas import (
    EloPoint,
    OpeningStat,
    OpeningsResponse,
    OverviewResponse,
    PatternStat,
    PatternsResponse,
    StyleMatchResponse,
)
from services.pattern_stats import compute_patterns
from services.style_matcher import compute_style_match

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    username: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    # Summary counts
    result = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
            func.sum(case((Game.result == "loss", 1), else_=0)).label("losses"),
            func.sum(case((Game.result == "draw", 1), else_=0)).label("draws"),
            func.avg(Game.avg_cpl).label("avg_cpl"),
        ).where(Game.username == username)
    )
    row = result.one()
    total = row.total or 0
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No games found for '{username}'")

    wins = int(row.wins or 0)
    losses = int(row.losses or 0)
    draws = int(row.draws or 0)
    avg_cpl = round(float(row.avg_cpl), 1) if row.avg_cpl else None
    win_rate = round(wins / total, 3) if total > 0 else 0.0

    # ELO trend — last 50 games with elo data, chronological
    elo_result = await session.execute(
        select(Game.played_at, Game.user_elo)
        .where(Game.username == username, Game.user_elo != None)  # noqa: E711
        .order_by(Game.played_at.asc())
        .limit(50)
    )
    elo_rows = elo_result.all()
    elo_trend = [
        EloPoint(date=r.played_at.strftime("%Y-%m-%d") if r.played_at else "?", elo=r.user_elo)
        for r in elo_rows
        if r.user_elo
    ]

    current_elo: Optional[int] = None
    if elo_trend:
        current_elo = elo_trend[-1].elo

    return OverviewResponse(
        username=username,
        total_games=total,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=win_rate,
        avg_cpl=avg_cpl,
        elo_trend=elo_trend,
        current_elo=current_elo,
    )


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(
    username: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    # Get current user ELO for tier relevance
    elo_result = await session.execute(
        select(Game.user_elo)
        .where(Game.username == username, Game.user_elo != None)  # noqa: E711
        .order_by(Game.played_at.desc())
        .limit(1)
    )
    elo_row = elo_result.scalar_one_or_none()

    patterns = await compute_patterns(session, username, elo_row)
    pattern_stats = [
        PatternStat(
            feature=p.feature,
            label=p.label,
            win_rate_with=p.win_rate_with,
            win_rate_without=p.win_rate_without,
            delta=p.delta,
            sample_size_with=p.sample_size_with,
            sample_size_without=p.sample_size_without,
            is_significant=p.is_significant,
            elo_relevant=p.elo_relevant,
        )
        for p in patterns
    ]
    return PatternsResponse(username=username, patterns=pattern_stats)


@router.get("/openings", response_model=OpeningsResponse)
async def get_openings(
    username: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(
            Game.opening_eco,
            Game.opening_name,
            func.count(Game.id).label("games"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
            func.sum(case((Game.result == "loss", 1), else_=0)).label("losses"),
            func.sum(case((Game.result == "draw", 1), else_=0)).label("draws"),
        )
        .where(Game.username == username, Game.opening_eco != None)  # noqa: E711
        .group_by(Game.opening_eco, Game.opening_name)
        .order_by(desc("games"))
        .limit(20)
    )
    rows = result.all()

    openings = []
    for row in rows:
        games = row.games or 0
        wins = int(row.wins or 0)
        losses = int(row.losses or 0)
        draws = int(row.draws or 0)
        win_rate = round(wins / games, 3) if games > 0 else 0.0
        openings.append(OpeningStat(
            eco=row.opening_eco or "",
            name=row.opening_name or "Unknown",
            games=games,
            wins=wins,
            losses=losses,
            draws=draws,
            win_rate=win_rate,
        ))

    return OpeningsResponse(username=username, openings=openings)


@router.get("/style", response_model=StyleMatchResponse)
async def get_style(
    username: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    match = await compute_style_match(session, username)
    if match is None:
        raise HTTPException(
            status_code=422,
            detail="Not enough game data to compute style match (need at least 5 analysed games).",
        )
    return match
