"""Application startup script."""
# pragma: no cover
# pylint: disable=broad-except
import argparse
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


def _get_uvicorn_config() -> uvicorn.Config:
    reload = (
        settings.server.RELOAD
        if settings.server.RELOAD is not None
        else settings.app.ENVIRONMENT == "local"
    )
    reload_dirs = settings.server.RELOAD_DIRS if reload else None

    return uvicorn.Config(
        app=settings.server.APP_LOC,
        factory=settings.server.APP_LOC_IS_FACTORY,
        host=settings.server.HOST,
        loop="none",
        port=settings.server.PORT,
        reload=reload,
        reload_dirs=reload_dirs,
        timeout_keep_alive=settings.server.KEEPALIVE,
    )


async def _run_server(config: uvicorn.Config) -> None:
    """Run an uvicorn server with the given config."""
    server = uvicorn.Server(config)
    await server.serve()


def run_app() -> None:
    """Run the application."""
    parser = argparse.ArgumentParser(description="Run the application")
    parser.add_argument("--no-db", action="store_const", const=False, default=True, dest="check_db")
    parser.add_argument(
        "--no-cache", action="store_const", const=False, default=True, dest="check_cache"
    )
    args = parser.parse_args()

    with asyncio.Runner() as runner:
        if args.check_db:
            runner.run(_db_ready())
        if args.check_cache:
            runner.run(_redis_ready())
        runner.run(_run_server(_get_uvicorn_config()))
