"""SQLAlchemy 2.0 async models and engine setup."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = "sqlite+aiosqlite:///./chess_analyzer.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    games: Mapped[list["Game"]] = relationship("Game", back_populates="user_ref", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), ForeignKey("users.username"), index=True)
    user_color: Mapped[str] = mapped_column(String(5))  # "white" or "black"
    result: Mapped[str] = mapped_column(String(4))  # "win", "loss", "draw"
    user_elo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opponent_elo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_control: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    opening_eco: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    opening_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    played_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    raw_pgn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Feature columns
    queen_trade_move: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    castled_kingside: Mapped[bool] = mapped_column(Boolean, default=False)
    castled_queenside: Mapped[bool] = mapped_column(Boolean, default=False)
    castled_never: Mapped[bool] = mapped_column(Boolean, default=True)
    castle_move: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    central_control_move15: Mapped[bool] = mapped_column(Boolean, default=False)
    pieces_developed_by_10: Mapped[int] = mapped_column(Integer, default=0)
    avg_cpl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    blunders: Mapped[int] = mapped_column(Integer, default=0)
    mistakes: Mapped[int] = mapped_column(Integer, default=0)
    inaccuracies: Mapped[int] = mapped_column(Integer, default=0)
    time_pressure_blunders: Mapped[int] = mapped_column(Integer, default=0)
    has_evals: Mapped[bool] = mapped_column(Boolean, default=False)
    # Style sub-metrics
    piece_exchange_preference: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    queen_activity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pawn_advance_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(10), default="pending")

    user_ref: Mapped["User"] = relationship("User", back_populates="games")
    positions: Mapped[list["Position"]] = relationship("Position", back_populates="game_ref", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_games_username_result", "username", "result"),
        Index("ix_games_username_played_at", "username", "played_at"),
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(20), ForeignKey("games.game_id"), index=True)
    move_number: Mapped[int] = mapped_column(Integer)
    fen: Mapped[str] = mapped_column(String(200))
    eval_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_move: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    played_move: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cpl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_blunder: Mapped[bool] = mapped_column(Boolean, default=False)
    is_puzzle_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    clock_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    game_ref: Mapped["Game"] = relationship("Game", back_populates="positions")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, done, error
    total_games: Mapped[int] = mapped_column(Integer, default=0)
    processed_games: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
