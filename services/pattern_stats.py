"""Compute win-rate correlations per feature across a user's game set."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Game

# ─── ELO tier relevance map ───────────────────────────────────────────────────

_TIER_PATTERNS: dict[str, list[str]] = {
    "beginner": [
        "castled_never", "hanging_piece_blunder", "queen_early",
        "blunder_rate_high",
    ],
    "intermediate": [
        "castled_never", "central_control_move15", "development_slow",
        "blunder_rate_high", "time_pressure_blunders",
    ],
    "advanced": [
        "queen_trade_timing", "central_control_move15", "time_pressure_blunders",
        "development_slow",
    ],
    "expert": [
        "piece_exchange_preference", "queen_activity_score", "endgame_entry",
    ],
}

_FEATURE_LABELS: dict[str, str] = {
    "castled_kingside": "Castled Kingside",
    "castled_queenside": "Castled Queenside",
    "castled_never": "Never Castled",
    "central_control_move15": "Central Pawn at Move 15",
    "has_evals": "Game Has Engine Evals",
    "queen_trade_early": "Early Queen Trade (< move 20)",
    "development_slow": "Slow Development (< 3 pieces by move 10)",
    "blunder_free": "No Blunders",
    "time_pressure_blunders": "Blunders Under Time Pressure",
}


def _get_tier(elo: Optional[int]) -> str:
    if elo is None or elo < 1300:
        return "beginner"
    if elo < 1700:
        return "intermediate"
    if elo < 2000:
        return "advanced"
    return "expert"


@dataclass
class PatternResult:
    feature: str
    label: str
    win_rate_with: float
    win_rate_without: float
    delta: float
    sample_size_with: int
    sample_size_without: int
    is_significant: bool
    elo_relevant: bool


async def compute_patterns(
    session: AsyncSession,
    username: str,
    user_elo: Optional[int],
) -> list[PatternResult]:
    """
    For each boolean feature on Game, compute win-rate correlation.
    Returns list sorted by abs(delta) descending.
    """
    tier = _get_tier(user_elo)
    tier_relevant = _TIER_PATTERNS.get(tier, [])

    # Boolean feature columns to analyse
    bool_features: list[tuple[str, str]] = [
        ("castled_kingside", "Castled Kingside"),
        ("castled_queenside", "Castled Queenside"),
        ("castled_never", "Never Castled"),
        ("central_control_move15", "Central Pawn at Move 15"),
    ]

    results: list[PatternResult] = []

    for col_name, label in bool_features:
        col = getattr(Game, col_name, None)
        if col is None:
            continue

        # Win counts and totals for feature=True
        q_with = await session.execute(
            select(
                func.count(Game.id).label("total"),
                func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
            ).where(Game.username == username, col == True)  # noqa: E712
        )
        row_with = q_with.one()

        # Win counts and totals for feature=False
        q_without = await session.execute(
            select(
                func.count(Game.id).label("total"),
                func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
            ).where(Game.username == username, col == False)  # noqa: E712
        )
        row_without = q_without.one()

        total_with = row_with.total or 0
        wins_with = int(row_with.wins or 0)
        total_without = row_without.total or 0
        wins_without = int(row_without.wins or 0)

        if total_with == 0 and total_without == 0:
            continue

        win_rate_with = wins_with / total_with if total_with > 0 else 0.0
        win_rate_without = wins_without / total_without if total_without > 0 else 0.0
        delta = win_rate_with - win_rate_without
        is_significant = total_with >= 10 and total_without >= 5

        results.append(PatternResult(
            feature=col_name,
            label=label,
            win_rate_with=round(win_rate_with, 3),
            win_rate_without=round(win_rate_without, 3),
            delta=round(delta, 3),
            sample_size_with=total_with,
            sample_size_without=total_without,
            is_significant=is_significant,
            elo_relevant=col_name in tier_relevant,
        ))

    # Derived patterns from numeric fields
    derived = await _compute_derived_patterns(session, username, user_elo, tier_relevant)
    results.extend(derived)

    results.sort(key=lambda r: abs(r.delta), reverse=True)
    return results


async def _compute_derived_patterns(
    session: AsyncSession,
    username: str,
    user_elo: Optional[int],
    tier_relevant: list[str],
) -> list[PatternResult]:
    """Compute patterns derived from numeric columns via thresholds."""
    results: list[PatternResult] = []

    # Blunder-free games
    q_bf = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.blunders == 0)
    )
    q_bf_not = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.blunders > 0)
    )
    results.append(_make_pattern(
        "blunder_free", "No Blunders",
        q_bf.one(), q_bf_not.one(), tier_relevant
    ))

    # Slow development: fewer than 3 minor pieces developed by move 10
    q_slow = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.pieces_developed_by_10 < 3)
    )
    q_fast = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.pieces_developed_by_10 >= 3)
    )
    results.append(_make_pattern(
        "development_slow", "Slow Development (< 3 pieces by move 10)",
        q_slow.one(), q_fast.one(), tier_relevant
    ))

    # Time pressure blunders
    q_tp = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.time_pressure_blunders > 0)
    )
    q_no_tp = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(Game.username == username, Game.time_pressure_blunders == 0)
    )
    results.append(_make_pattern(
        "time_pressure_blunders", "Blunders Under Time Pressure",
        q_tp.one(), q_no_tp.one(), tier_relevant
    ))

    # Early queen trade (queen trade move < 40 half-moves = move 20)
    q_qt = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(
            Game.username == username,
            Game.queen_trade_move != None,  # noqa: E711
            Game.queen_trade_move < 40,
        )
    )
    q_no_qt = await session.execute(
        select(
            func.count(Game.id).label("total"),
            func.sum(case((Game.result == "win", 1), else_=0)).label("wins"),
        ).where(
            Game.username == username,
            (Game.queen_trade_move == None) | (Game.queen_trade_move >= 40),  # noqa: E711
        )
    )
    results.append(_make_pattern(
        "queen_trade_early", "Early Queen Trade (before move 20)",
        q_qt.one(), q_no_qt.one(), tier_relevant
    ))

    return [r for r in results if r is not None]


def _make_pattern(
    feature: str,
    label: str,
    row_with,
    row_without,
    tier_relevant: list[str],
) -> PatternResult:
    total_with = row_with.total or 0
    wins_with = int(row_with.wins or 0)
    total_without = row_without.total or 0
    wins_without = int(row_without.wins or 0)

    win_rate_with = wins_with / total_with if total_with > 0 else 0.0
    win_rate_without = wins_without / total_without if total_without > 0 else 0.0
    delta = win_rate_with - win_rate_without
    is_significant = total_with >= 10

    return PatternResult(
        feature=feature,
        label=label,
        win_rate_with=round(win_rate_with, 3),
        win_rate_without=round(win_rate_without, 3),
        delta=round(delta, 3),
        sample_size_with=total_with,
        sample_size_without=total_without,
        is_significant=is_significant,
        elo_relevant=feature in tier_relevant,
    )
