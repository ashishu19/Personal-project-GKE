"""PGN → ParsedGame: single-pass move walker using python-chess."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import chess
import chess.pgn
import io

# Regex patterns for comment annotations
_EVAL_RE = re.compile(r"\[%eval\s+([#\-\d.]+)\]")
_CLK_RE = re.compile(r"\[%clk\s+(\d+:\d+:\d+)\]")


def _parse_eval(raw: str) -> Optional[float]:
    """Parse %eval annotation. Mate scores → ±1000."""
    if raw.startswith("#"):
        # Mate in N — positive means white wins, negative means black wins
        n = int(raw[1:])
        return 1000.0 if n > 0 else -1000.0
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_clk(raw: str) -> Optional[float]:
    """Parse %clk H:MM:SS → total seconds."""
    parts = raw.split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    except ValueError:
        return None


def _safe_int(val: str) -> Optional[int]:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


@dataclass
class ParsedMove:
    move_number: int          # half-move index from game start
    san: str
    uci: str
    fen_after: str            # FEN after this move
    eval_score: Optional[float] = None   # from %eval, White's perspective
    clock_seconds: Optional[float] = None
    cpl: Optional[float] = None  # computed after parsing


@dataclass
class ParsedGame:
    game_id: str
    username: str
    user_color: str           # "white" | "black"
    result: str               # "win" | "loss" | "draw"
    user_elo: Optional[int]
    opponent_elo: Optional[int]
    time_control: Optional[str]
    opening_eco: Optional[str]
    opening_name: Optional[str]
    played_at: Optional[datetime]
    raw_pgn: str
    moves: list[ParsedMove] = field(default_factory=list)
    has_evals: bool = False


def parse_pgn(pgn_text: str, username: str) -> Optional[ParsedGame]:
    """Parse a single PGN string into a ParsedGame. Returns None on failure."""
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
    except Exception:
        return None
    if game is None:
        return None

    headers = game.headers

    # Extract game ID from Site header
    site = headers.get("Site", "")
    game_id = site.rstrip("/").split("/")[-1] if site else ""
    if not game_id:
        return None

    # Determine user color
    white_player = headers.get("White", "").lower()
    user_lower = username.lower()
    user_color = "white" if white_player == user_lower else "black"

    # Determine result
    raw_result = headers.get("Result", "*")
    if raw_result == "1-0":
        result = "win" if user_color == "white" else "loss"
    elif raw_result == "0-1":
        result = "win" if user_color == "black" else "loss"
    elif raw_result == "1/2-1/2":
        result = "draw"
    else:
        result = "draw"

    # ELO
    if user_color == "white":
        user_elo = _safe_int(headers.get("WhiteElo", "?"))
        opp_elo = _safe_int(headers.get("BlackElo", "?"))
    else:
        user_elo = _safe_int(headers.get("BlackElo", "?"))
        opp_elo = _safe_int(headers.get("WhiteElo", "?"))

    # Opening
    eco = headers.get("ECO") or None
    opening_name = headers.get("Opening") or None

    # Time control
    time_control = headers.get("TimeControl") or None

    # Date
    date_str = headers.get("UTCDate", headers.get("Date", ""))
    time_str = headers.get("UTCTime", "")
    played_at: Optional[datetime] = None
    if date_str and date_str != "????.??.??":
        try:
            dt_str = f"{date_str} {time_str}".strip()
            played_at = datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
        except ValueError:
            try:
                played_at = datetime.strptime(date_str, "%Y.%m.%d")
            except ValueError:
                played_at = None

    # Single-pass move walk
    moves: list[ParsedMove] = []
    board = game.board()
    half_move_idx = 0

    for node in game.mainline():
        move = node.move
        san = board.san(move)
        uci = move.uci()
        board.push(move)
        fen_after = board.fen()

        comment = node.comment or ""
        eval_match = _EVAL_RE.search(comment)
        clk_match = _CLK_RE.search(comment)

        eval_score = _parse_eval(eval_match.group(1)) if eval_match else None
        clock_seconds = _parse_clk(clk_match.group(1)) if clk_match else None

        moves.append(ParsedMove(
            move_number=half_move_idx,
            san=san,
            uci=uci,
            fen_after=fen_after,
            eval_score=eval_score,
            clock_seconds=clock_seconds,
        ))
        half_move_idx += 1

    has_evals = any(m.eval_score is not None for m in moves)

    # Compute CPL: compare each user move's eval to previous eval
    # %eval is from White's perspective; for Black moves, invert
    if has_evals:
        for i, move in enumerate(moves):
            is_white_move = (move.move_number % 2 == 0)
            is_user_move = (user_color == "white") == is_white_move

            if not is_user_move:
                continue
            if move.eval_score is None:
                continue

            # Find previous eval
            prev_eval: Optional[float] = None
            for j in range(i - 1, -1, -1):
                if moves[j].eval_score is not None:
                    prev_eval = moves[j].eval_score
                    break

            if prev_eval is None:
                continue

            # %eval is always from White's perspective (positive = White is better).
            # CPL = how much the position worsened for the user after their move.
            #   White: good move → eval stays or rises → CPL ≤ 0 → clamped to 0
            #           bad move  → eval drops           → CPL > 0
            #   Black: good move → eval drops (worse for White) → CPL ≤ 0 → clamped to 0
            #           bad move  → eval rises (better for White) → CPL > 0
            if user_color == "white":
                cpl = (prev_eval - move.eval_score) * 100
            else:
                cpl = (move.eval_score - prev_eval) * 100

            move.cpl = max(0.0, cpl)  # centipawns, clamped at 0

    return ParsedGame(
        game_id=game_id,
        username=username,
        user_color=user_color,
        result=result,
        user_elo=user_elo,
        opponent_elo=opp_elo,
        time_control=time_control,
        opening_eco=eco,
        opening_name=opening_name,
        played_at=played_at,
        raw_pgn=pgn_text,
        moves=moves,
        has_evals=has_evals,
    )
