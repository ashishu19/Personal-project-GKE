"""Pydantic v2 response schemas for all endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ─── Import ───────────────────────────────────────────────────────────────────

class ImportStartResponse(BaseModel):
    job_id: str
    username: str
    message: str


class ImportStatusResponse(BaseModel):
    job_id: str
    username: str
    status: str  # pending, running, done, error
    total_games: int
    processed_games: int
    progress_pct: float
    error_message: Optional[str] = None


# ─── Stats ────────────────────────────────────────────────────────────────────

class EloPoint(BaseModel):
    date: str
    elo: int


class OverviewResponse(BaseModel):
    username: str
    total_games: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_cpl: Optional[float]
    elo_trend: list[EloPoint]
    current_elo: Optional[int]


class PatternStat(BaseModel):
    feature: str
    label: str
    win_rate_with: float
    win_rate_without: float
    delta: float
    sample_size_with: int
    sample_size_without: int
    is_significant: bool
    elo_relevant: bool


class PatternsResponse(BaseModel):
    username: str
    patterns: list[PatternStat]


class OpeningStat(BaseModel):
    eco: str
    name: str
    games: int
    wins: int
    losses: int
    draws: int
    win_rate: float


class OpeningsResponse(BaseModel):
    username: str
    openings: list[OpeningStat]


class StyleVector(BaseModel):
    piece_exchange_preference: float
    queen_activity: float
    pawn_advance_rate: float
    tactical_complexity: float
    endgame_entry_rate: float


class StyleMatchResponse(BaseModel):
    username: str
    matched_gm: str
    gm_title: str
    archetype: str
    similarity_score: float
    description: str
    study_tip: str
    user_style_vector: StyleVector


# ─── Games ────────────────────────────────────────────────────────────────────

class GameSummary(BaseModel):
    game_id: str
    user_color: str
    result: str
    user_elo: Optional[int]
    opponent_elo: Optional[int]
    time_control: Optional[str]
    opening_eco: Optional[str]
    opening_name: Optional[str]
    played_at: Optional[datetime]
    avg_cpl: Optional[float]
    blunders: int
    has_evals: bool


class GamesListResponse(BaseModel):
    username: str
    total: int
    page: int
    page_size: int
    games: list[GameSummary]


class PositionDetail(BaseModel):
    move_number: int
    fen: str
    eval_score: Optional[float]
    best_move: Optional[str]
    played_move: Optional[str]
    cpl: Optional[float]
    is_blunder: bool
    is_puzzle_candidate: bool
    clock_seconds: Optional[float]


class GameDetailResponse(BaseModel):
    game_id: str
    username: str
    user_color: str
    result: str
    user_elo: Optional[int]
    opponent_elo: Optional[int]
    time_control: Optional[str]
    opening_eco: Optional[str]
    opening_name: Optional[str]
    played_at: Optional[datetime]
    raw_pgn: Optional[str]
    avg_cpl: Optional[float]
    blunders: int
    mistakes: int
    inaccuracies: int
    has_evals: bool
    positions: list[PositionDetail]


# ─── Puzzles ──────────────────────────────────────────────────────────────────

class PuzzleResponse(BaseModel):
    puzzle_id: int
    game_id: str
    move_number: int
    fen: str
    eval_before: Optional[float]
    solved: bool = False


class PuzzleSolveRequest(BaseModel):
    move_uci: str


class PuzzleSolveResponse(BaseModel):
    correct: bool
    solution_uci: Optional[str]
    solution_san: Optional[str]
    explanation: str


# ─── Suggestions ─────────────────────────────────────────────────────────────

class SuggestionsRequest(BaseModel):
    username: str
