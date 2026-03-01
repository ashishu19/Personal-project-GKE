"""GET /api/puzzles/{username} and POST /api/puzzles/{id}/solve"""
from __future__ import annotations

import chess
import chess.pgn

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Position, get_session
from models.schemas import PuzzleResponse, PuzzleSolveRequest, PuzzleSolveResponse

router = APIRouter(prefix="/api/puzzles", tags=["puzzles"])


@router.get("/{username}", response_model=list[PuzzleResponse])
async def list_puzzles(
    username: str,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """Return unsolved puzzle candidates from the user's games."""
    from models.database import Game
    result = await session.execute(
        select(Position)
        .join(Game, Game.game_id == Position.game_id)
        .where(
            Game.username == username,
            Position.is_puzzle_candidate == True,  # noqa: E712
        )
        .limit(limit)
    )
    positions = result.scalars().all()

    return [
        PuzzleResponse(
            puzzle_id=p.id,
            game_id=p.game_id,
            move_number=p.move_number,
            fen=p.fen,
            eval_before=p.eval_score,
            solved=False,
        )
        for p in positions
    ]


@router.post("/{puzzle_id}/solve", response_model=PuzzleSolveResponse)
async def solve_puzzle(
    puzzle_id: int,
    body: PuzzleSolveRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Position).where(Position.id == puzzle_id)
    )
    pos = result.scalar_one_or_none()
    if pos is None:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    solution_uci = pos.best_move
    if solution_uci is None:
        raise HTTPException(status_code=422, detail="No solution available for this puzzle")

    # Validate submitted move against solution
    correct = body.move_uci.strip().lower() == solution_uci.strip().lower()

    # Convert solution to SAN for display
    solution_san: str | None = None
    try:
        board = chess.Board(pos.fen)
        move = chess.Move.from_uci(solution_uci)
        solution_san = board.san(move)
    except Exception:
        solution_san = solution_uci

    if correct:
        explanation = (
            f"Correct! The best move was {solution_san}. "
            "You found the key resource in this position."
        )
    else:
        explanation = (
            f"Not quite. The best move was {solution_san}. "
            "Study why this move is stronger — consider piece activity and king safety."
        )

    return PuzzleSolveResponse(
        correct=correct,
        solution_uci=solution_uci,
        solution_san=solution_san,
        explanation=explanation,
    )
