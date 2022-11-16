"""Application startup script."""
# pragma: no cover
# pylint: disable=broad-except
import asyncio

import uvicorn
import uvloop
from sqlalchemy import text

from starlite_saqlalchemy import redis, settings
from starlite_saqlalchemy.db import engine

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


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
    uvicorn_config = uvicorn.Config(
        app=settings.server.APP_LOC,
        factory=settings.server.APP_LOC_IS_FACTORY,
        host=settings.server.HOST,
        loop="none",
        port=settings.server.PORT,
        reload=settings.server.RELOAD,
        reload_dirs=settings.server.RELOAD_DIRS,
        timeout_keep_alive=settings.server.KEEPALIVE,
    )
    server = uvicorn.Server(config=uvicorn_config)
    with asyncio.Runner() as runner:
        runner.run(_db_ready())
        runner.run(_redis_ready())
        runner.run(server.serve())
