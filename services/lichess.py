"""Lichess API async streaming client."""
import asyncio
import logging
from collections.abc import AsyncIterator

import httpx

logger = logging.getLogger(__name__)

LICHESS_BASE = "https://lichess.org"


async def stream_user_games(
    username: str,
    max_games: int = 100,
    token: str | None = None,
) -> AsyncIterator[str]:
    """
    Stream PGN games for a user from the Lichess bulk export API.
    Yields individual PGN strings (one per game).

    The endpoint returns multiple PGNs concatenated, separated by blank lines.
    We buffer and split on double-newline between games (each game starts with [Event).
    """
    url = f"{LICHESS_BASE}/api/games/user/{username}"
    params = {
        "max": max_games,
        "evals": "true",
        "clocks": "true",
        "opening": "true",
        "pgnInJson": "false",
    }
    headers = {"Accept": "application/x-chess-pgn"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("GET", url, params=params, headers=headers) as resp:
                resp.raise_for_status()
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    # Split on double newline — games are separated by \n\n
                    while "\n\n\n" in buffer or (buffer.count("[Event") > 1):
                        # Find boundary between games: second occurrence of [Event
                        idx = buffer.find("[Event", 1)
                        if idx == -1:
                            break
                        # Ensure there's a blank line before the next [Event
                        blank_idx = buffer.rfind("\n\n", 0, idx)
                        if blank_idx == -1:
                            break
                        pgn = buffer[:blank_idx].strip()
                        buffer = buffer[blank_idx:].lstrip("\n")
                        if pgn:
                            yield pgn
                        await asyncio.sleep(0)  # yield control

                # Yield remaining content
                remaining = buffer.strip()
                if remaining and "[Event" in remaining:
                    yield remaining

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Lichess user '{username}' not found") from e
            raise
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to reach Lichess: {e}") from e
