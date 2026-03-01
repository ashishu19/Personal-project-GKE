"""Rule-based feature extraction from a ParsedGame — single board replay pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import chess

from services.pgn_parser import ParsedGame, ParsedMove


# ─── ELO-normalised CPL thresholds ───────────────────────────────────────────

def _get_thresholds(elo: Optional[int]) -> tuple[int, int, int]:
    """Return (blunder, mistake, inaccuracy) CPL thresholds for given ELO."""
    if elo is None or elo < 1300:
        return 250, 150, 75
    if elo < 1700:
        return 200, 100, 50
    if elo < 2000:
        return 150, 75, 35
    return 100, 50, 25


# ─── Extracted features ───────────────────────────────────────────────────────

@dataclass
class ExtractedFeatures:
    queen_trade_move: Optional[int]        # half-move index when both queens left board
    castled_kingside: bool
    castled_queenside: bool
    castled_never: bool
    castle_move: Optional[int]             # half-move when user castled
    central_control_move15: bool           # user has pawn on central squares at move 15
    pieces_developed_by_10: int            # minor pieces off back rank by move 10
    avg_cpl: Optional[float]
    blunders: int
    mistakes: int
    inaccuracies: int
    time_pressure_blunders: int            # blunders with < 30s on clock
    piece_exchange_preference: float       # [-1 avoids trades, +1 seeks trades]
    queen_activity_score: float            # [0..1] queen moved early / often
    pawn_advance_rate: float               # fraction of user moves that are pawn pushes
    puzzle_candidates: list[int]           # half-move indices of puzzle candidates


def extract_features(game: ParsedGame) -> ExtractedFeatures:
    """
    Replay the game board once and compute all features.
    Returns an ExtractedFeatures instance.
    """
    moves = game.moves
    user_color = chess.WHITE if game.user_color == "white" else chess.BLACK
    elo = game.user_elo
    blunder_thresh, mistake_thresh, inaccuracy_thresh = _get_thresholds(elo)

    # Initialise board
    board = chess.Board()

    # Tracking state
    queen_trade_move: Optional[int] = None
    castled_kingside = False
    castled_queenside = False
    castle_move: Optional[int] = None
    central_control_move15 = False
    pieces_developed_by_10 = 0

    blunders = 0
    mistakes = 0
    inaccuracies = 0
    time_pressure_blunders = 0

    user_cpls: list[float] = []
    user_move_count = 0
    pawn_move_count = 0
    queen_move_count = 0
    piece_captures = 0   # captures by user (proxy for exchange seeking)

    puzzle_candidates: list[int] = []

    for i, pm in enumerate(moves):
        try:
            move = chess.Move.from_uci(pm.uci)
        except ValueError:
            continue  # Skip unparseable moves; board state stays consistent

        is_white_move = (i % 2 == 0)
        is_user_move = (user_color == chess.WHITE) == is_white_move

        # ── Feature: Queen trade ──────────────────────────────────────────────
        if queen_trade_move is None:
            white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
            black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
            if white_queens == 0 and black_queens == 0:
                queen_trade_move = i

        # ── Feature: Castling ─────────────────────────────────────────────────
        if is_user_move and castle_move is None:
            if board.is_kingside_castling(move):
                castled_kingside = True
                castle_move = i
            elif board.is_queenside_castling(move):
                castled_queenside = True
                castle_move = i

        # ── Feature: Central control at move 15 ──────────────────────────────
        full_move = (i // 2) + 1
        if full_move == 15 and not is_user_move:
            # Check after user's move 15 was played (opponent is about to move)
            center_squares = [chess.E4, chess.D4] if user_color == chess.WHITE else [chess.E5, chess.D5]
            central_control_move15 = any(
                board.piece_at(sq) == chess.Piece(chess.PAWN, user_color)
                for sq in center_squares
            )

        # ── Feature: Development by move 10 ──────────────────────────────────
        if full_move == 10 and not is_user_move:
            back_rank = chess.BB_RANK_1 if user_color == chess.WHITE else chess.BB_RANK_8
            minor_pieces = board.pieces(chess.KNIGHT, user_color) | board.pieces(chess.BISHOP, user_color)
            pieces_developed_by_10 = bin(minor_pieces & ~back_rank).count("1")

        # ── Feature: Pawn advance rate ────────────────────────────────────────
        if is_user_move:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                pawn_move_count += 1
            if piece and piece.piece_type == chess.QUEEN:
                queen_move_count += 1
            user_move_count += 1

            # Capture tracking
            if board.is_capture(move):
                piece_captures += 1

        # ── Push move ─────────────────────────────────────────────────────────
        board.push(move)

        # ── Feature: CPL / blunders / mistakes ───────────────────────────────
        if is_user_move and pm.cpl is not None:
            cpl = pm.cpl
            user_cpls.append(cpl)

            is_blunder = cpl >= blunder_thresh
            is_mistake = not is_blunder and cpl >= mistake_thresh
            is_inaccuracy = not is_blunder and not is_mistake and cpl >= inaccuracy_thresh

            if is_blunder:
                blunders += 1
                if pm.clock_seconds is not None and pm.clock_seconds < 30:
                    time_pressure_blunders += 1
            elif is_mistake:
                mistakes += 1
            elif is_inaccuracy:
                inaccuracies += 1

            # Puzzle candidate: user blundered in roughly equal position
            if is_blunder and pm.eval_score is not None and abs(pm.eval_score) <= 1.5:
                puzzle_candidates.append(i)

    # ── Aggregate features ────────────────────────────────────────────────────
    avg_cpl = sum(user_cpls) / len(user_cpls) if user_cpls else None
    castled_never = not castled_kingside and not castled_queenside
    pawn_advance_rate = pawn_move_count / user_move_count if user_move_count > 0 else 0.0
    queen_activity_score = min(1.0, queen_move_count / max(1, user_move_count) * 5)

    # piece_exchange_preference: normalise captures per user move [-1..+1] → map to [0..1]
    # -1 = avoids trades, +1 = aggressively trades
    capture_rate = piece_captures / max(1, user_move_count)
    piece_exchange_preference = min(1.0, max(-1.0, (capture_rate - 0.15) / 0.15))

    return ExtractedFeatures(
        queen_trade_move=queen_trade_move,
        castled_kingside=castled_kingside,
        castled_queenside=castled_queenside,
        castled_never=castled_never,
        castle_move=castle_move,
        central_control_move15=central_control_move15,
        pieces_developed_by_10=pieces_developed_by_10,
        avg_cpl=avg_cpl,
        blunders=blunders,
        mistakes=mistakes,
        inaccuracies=inaccuracies,
        time_pressure_blunders=time_pressure_blunders,
        piece_exchange_preference=piece_exchange_preference,
        queen_activity_score=queen_activity_score,
        pawn_advance_rate=pawn_advance_rate,
        puzzle_candidates=puzzle_candidates,
    )
