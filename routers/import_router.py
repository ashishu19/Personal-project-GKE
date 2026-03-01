"""POST /api/import/{username} and GET /api/import/status/{job_id}."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import AnalysisJob, Game, Position, User, get_session
from models.schemas import ImportStartResponse, ImportStatusResponse
from services.feature_extractor import extract_features
from services.lichess import stream_user_games
from services.pgn_parser import parse_pgn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/import", tags=["import"])


async def _run_import(
    job_id: str,
    username: str,
    max_games: int,
    token: str | None,
) -> None:
    """Background task: stream games, parse, extract features, persist."""
    from models.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Mark job as running
        result = await session.execute(
            select(AnalysisJob).where(AnalysisJob.job_id == job_id)
        )
        job = result.scalar_one()
        job.status = "running"
        await session.commit()

        # Ensure user row exists
        user_result = await session.execute(
            select(User).where(User.username == username)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(username=username)
            session.add(user)
            await session.commit()

        processed = 0
        errors = 0

        try:
            async for pgn_text in stream_user_games(username, max_games, token):
                parsed = parse_pgn(pgn_text, username)
                if parsed is None:
                    errors += 1
                    continue

                # Skip if already imported
                existing = await session.execute(
                    select(Game).where(Game.game_id == parsed.game_id)
                )
                if existing.scalar_one_or_none() is not None:
                    processed += 1
                    job.processed_games = processed
                    await session.commit()
                    continue

                # Persist game
                game_row = Game(
                    game_id=parsed.game_id,
                    username=username,
                    user_color=parsed.user_color,
                    result=parsed.result,
                    user_elo=parsed.user_elo,
                    opponent_elo=parsed.opponent_elo,
                    time_control=parsed.time_control,
                    opening_eco=parsed.opening_eco,
                    opening_name=parsed.opening_name,
                    played_at=parsed.played_at,
                    raw_pgn=parsed.raw_pgn,
                    has_evals=parsed.has_evals,
                    analysis_status="pending",
                )
                session.add(game_row)

                # Persist positions
                for pm in parsed.moves:
                    pos = Position(
                        game_id=parsed.game_id,
                        move_number=pm.move_number,
                        fen=pm.fen_after,
                        eval_score=pm.eval_score,
                        played_move=pm.uci,
                        cpl=pm.cpl,
                        clock_seconds=pm.clock_seconds,
                    )
                    session.add(pos)

                await session.commit()

                # Feature extraction
                try:
                    features = extract_features(parsed)

                    # Update puzzle candidates
                    for half_move_idx in features.puzzle_candidates:
                        pos_result = await session.execute(
                            select(Position).where(
                                Position.game_id == parsed.game_id,
                                Position.move_number == half_move_idx,
                            )
                        )
                        pos_row = pos_result.scalar_one_or_none()
                        if pos_row:
                            pos_row.is_puzzle_candidate = True
                            pos_row.is_blunder = True

                    # Update game with features
                    game_row.queen_trade_move = features.queen_trade_move
                    game_row.castled_kingside = features.castled_kingside
                    game_row.castled_queenside = features.castled_queenside
                    game_row.castled_never = features.castled_never
                    game_row.castle_move = features.castle_move
                    game_row.central_control_move15 = features.central_control_move15
                    game_row.pieces_developed_by_10 = features.pieces_developed_by_10
                    game_row.avg_cpl = features.avg_cpl
                    game_row.blunders = features.blunders
                    game_row.mistakes = features.mistakes
                    game_row.inaccuracies = features.inaccuracies
                    game_row.time_pressure_blunders = features.time_pressure_blunders
                    game_row.piece_exchange_preference = features.piece_exchange_preference
                    game_row.queen_activity_score = features.queen_activity_score
                    game_row.pawn_advance_rate = features.pawn_advance_rate
                    game_row.analysis_status = "done"
                    await session.commit()

                except Exception as e:
                    logger.warning("Feature extraction failed for %s: %s", parsed.game_id, e)
                    game_row.analysis_status = "done"  # don't block progress
                    await session.commit()

                processed += 1
                job.processed_games = processed
                await session.commit()
                await asyncio.sleep(0.05)  # be polite

        except (ValueError, ConnectionError) as e:
            job.status = "error"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await session.commit()
            return

        except Exception as e:
            logger.exception("Unexpected error during import for %s", username)
            job.status = "error"
            job.error_message = f"Unexpected error: {e}"
            job.completed_at = datetime.utcnow()
            await session.commit()
            return

        job.status = "done"
        job.completed_at = datetime.utcnow()
        await session.commit()
        logger.info("Import complete for %s: %d games processed", username, processed)


@router.post("/{username}", response_model=ImportStartResponse)
async def start_import(
    username: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    max: int = Query(100, ge=1, le=300),
    token: str | None = Query(None, description="Optional Lichess OAuth token"),
):
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        job_id=job_id,
        username=username,
        status="pending",
        total_games=max,
    )
    session.add(job)
    await session.commit()

    background_tasks.add_task(_run_import, job_id, username, max, token)

    return ImportStartResponse(
        job_id=job_id,
        username=username,
        message=f"Import started for {username}. Poll /api/import/status/{job_id} for progress.",
    )


@router.get("/status/{job_id}", response_model=ImportStatusResponse)
async def get_import_status(
    job_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    total = job.total_games or 1
    progress_pct = round(job.processed_games / total * 100, 1)

    return ImportStatusResponse(
        job_id=job.job_id,
        username=job.username,
        status=job.status,
        total_games=job.total_games,
        processed_games=job.processed_games,
        progress_pct=progress_pct,
        error_message=job.error_message,
    )
