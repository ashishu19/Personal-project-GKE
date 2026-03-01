"""FastAPI application entry point."""
from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
load_dotenv()  # loads .env from the backend directory

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import init_db
from routers import import_router, stats_router, games_router, suggestions_router, puzzles_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database...")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Chess Analyzer API",
    description="Personal chess improvement app powered by Lichess and Claude AI.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router.router)
app.include_router(stats_router.router)
app.include_router(games_router.router)
app.include_router(suggestions_router.router)
app.include_router(puzzles_router.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
