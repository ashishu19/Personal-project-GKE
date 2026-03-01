"""GET /api/games and GET /api/games/{game_id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Game, Position, get_session
from models.schemas import (
    GameDetailResponse,
    GameSummary,
    GamesListResponse,
    PositionDetail,
)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=GamesListResponse)
async def list_games(
    username: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    result: str | None = Query(None, description="Filter: win|loss|draw"),
    opening: str | None = Query(None, description="Filter by ECO code prefix e.g. B20"),
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * page_size
    base_filter = [Game.username == username]
    if result:
        base_filter.append(Game.result == result)
    if opening:
        base_filter.append(Game.opening_eco.startswith(opening))

    total_result = await session.execute(
        select(func.count(Game.id)).where(*base_filter)
    )
    total = total_result.scalar_one() or 0

    games_result = await session.execute(
        select(Game)
        .where(*base_filter)
        .order_by(desc(Game.played_at))
        .offset(offset)
        .limit(page_size)
    )
    games = games_result.scalars().all()

    summaries = [
        GameSummary(
            game_id=g.game_id,
            user_color=g.user_color,
            result=g.result,
            user_elo=g.user_elo,
            opponent_elo=g.opponent_elo,
            time_control=g.time_control,
            opening_eco=g.opening_eco,
            opening_name=g.opening_name,
            played_at=g.played_at,
            avg_cpl=g.avg_cpl,
            blunders=g.blunders,
            has_evals=g.has_evals,
        )
        for g in games
    ]

    return GamesListResponse(
        username=username,
        total=total,
        page=page,
        page_size=page_size,
        games=summaries,
    )


@router.get("/{game_id}", response_model=GameDetailResponse)
async def get_game(
    game_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Game).where(Game.game_id == game_id)
    )
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    pos_result = await session.execute(
        select(Position)
        .where(Position.game_id == game_id)
        .order_by(Position.move_number.asc())
    )
    positions = pos_result.scalars().all()

    position_details = [
        PositionDetail(
            move_number=p.move_number,
            fen=p.fen,
            eval_score=p.eval_score,
            best_move=p.best_move,
            played_move=p.played_move,
            cpl=p.cpl,
            is_blunder=p.is_blunder,
            is_puzzle_candidate=p.is_puzzle_candidate,
            clock_seconds=p.clock_seconds,
        )
        for p in positions
    ]

    return GameDetailResponse(
        game_id=game.game_id,
        username=game.username,
        user_color=game.user_color,
        result=game.result,
        user_elo=game.user_elo,
        opponent_elo=game.opponent_elo,
        time_control=game.time_control,
        opening_eco=game.opening_eco,
        opening_name=game.opening_name,
        played_at=game.played_at,
        raw_pgn=game.raw_pgn,
        avg_cpl=game.avg_cpl,
        blunders=game.blunders,
        mistakes=game.mistakes,
        inaccuracies=game.inaccuracies,
        has_evals=game.has_evals,
        positions=position_details,
    )
