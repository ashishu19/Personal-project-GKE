"""GM style vector cosine similarity matching."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Game
from models.schemas import StyleMatchResponse, StyleVector

_GM_DATA_PATH = Path(__file__).parent.parent / "data" / "gm_styles.json"
_gm_styles: dict | None = None


def _load_gm_styles() -> dict:
    global _gm_styles
    if _gm_styles is None:
        with open(_GM_DATA_PATH) as f:
            _gm_styles = json.load(f)
    return _gm_styles


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two style vectors (dicts)."""
    keys = set(a.keys()) & set(b.keys())
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(a[k] ** 2 for k in keys))
    mag_b = math.sqrt(sum(b[k] ** 2 for k in keys))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _normalise(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


async def compute_style_match(
    session: AsyncSession,
    username: str,
) -> Optional[StyleMatchResponse]:
    """
    Compute the user's style vector from game features and match against GM vectors.
    Returns None if insufficient data.
    """
    result = await session.execute(
        select(
            func.avg(Game.piece_exchange_preference).label("pep"),
            func.avg(Game.queen_activity_score).label("qa"),
            func.avg(Game.pawn_advance_rate).label("par"),
            func.avg(Game.avg_cpl).label("avg_cpl"),
            func.count(Game.id).label("total"),
            func.sum(Game.blunders).label("total_blunders"),
        ).where(
            Game.username == username,
            Game.analysis_status == "done",
            Game.piece_exchange_preference != None,  # noqa: E711
        )
    )
    row = result.one()
    total = row.total or 0

    if total < 5:
        return None

    pep = float(row.pep or 0.0)
    qa = float(row.qa or 0.0)
    par = float(row.par or 0.0)

    # Tactical complexity proxy: avg CPL inversely correlates — lower CPL = more precise = higher tactical ability
    avg_cpl = float(row.avg_cpl or 100.0)
    tactical_complexity = _normalise(1.0 - (avg_cpl / 200.0))

    # Endgame entry rate: fraction of games with queen trades
    qt_result = await session.execute(
        select(func.count(Game.id)).where(
            Game.username == username,
            Game.queen_trade_move != None,  # noqa: E711
        )
    )
    games_with_qt = qt_result.scalar_one() or 0
    endgame_entry_rate = _normalise(games_with_qt / max(1, total), 0.0, 1.0)

    user_vector = {
        "piece_exchange_preference": _normalise(pep),
        "queen_activity": _normalise(qa, 0.0, 1.0),
        "pawn_advance_rate": _normalise(par, 0.0, 1.0),
        "tactical_complexity": tactical_complexity,
        "endgame_entry_rate": endgame_entry_rate,
    }

    gm_styles = _load_gm_styles()
    best_key: str = ""
    best_score: float = -1.0

    for key, gm in gm_styles.items():
        sv = gm["style_vector"]
        score = _cosine_similarity(user_vector, sv)
        if score > best_score:
            best_score = score
            best_key = key

    if not best_key:
        return None

    matched = gm_styles[best_key]
    return StyleMatchResponse(
        username=username,
        matched_gm=matched["name"],
        gm_title=matched["title"],
        archetype=matched["archetype"],
        similarity_score=round(best_score, 3),
        description=matched["description"],
        study_tip=matched["study_tip"],
        user_style_vector=StyleVector(
            piece_exchange_preference=user_vector["piece_exchange_preference"],
            queen_activity=user_vector["queen_activity"],
            pawn_advance_rate=user_vector["pawn_advance_rate"],
            tactical_complexity=user_vector["tactical_complexity"],
            endgame_entry_rate=user_vector["endgame_entry_rate"],
        ),
    )
