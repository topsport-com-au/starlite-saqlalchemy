"""Application startup script."""
# pragma: no cover
# pylint: disable=broad-except
import asyncio

import uvicorn
from sqlalchemy import text

from starlite_saqlalchemy import redis, settings
from starlite_saqlalchemy.db import engine


async def _db_ready() -> None:
    """Wait for database to become responsive."""
    while True:
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:
            print(f"Waiting for DB: {exc}")
            await asyncio.sleep(5)
        else:
            print("DB OK!")
            break


async def _redis_ready() -> None:
    """Wait for redis to become responsive."""
    while True:
        try:
            await redis.client.ping()
        except Exception as exc:
            print(f"Waiting  for Redis: {exc}")
            await asyncio.sleep(5)
        else:
            print("Redis OK!")
            break


def run_app() -> None:
    """Run the application."""
    asyncio.run(_db_ready())
    asyncio.run(_redis_ready())
    uvicorn.run(
        settings.server.APP_LOC,
        host=settings.server.HOST,
        port=settings.server.PORT,
        reload=settings.server.RELOAD,
        reload_dirs=settings.server.RELOAD_DIRS,
        timeout_keep_alive=settings.server.KEEPALIVE,
    )
