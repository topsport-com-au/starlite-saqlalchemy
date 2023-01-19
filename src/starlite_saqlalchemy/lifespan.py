"""Application lifespan handlers."""
# pylint: disable=broad-except,import-outside-toplevel
import asyncio
import logging

import starlite

from starlite_saqlalchemy import constants, settings

logger = logging.getLogger(__name__)


async def _db_ready() -> None:
    """Wait for database to become responsive."""
    if constants.IS_SQLALCHEMY_INSTALLED:
        from sqlalchemy import text

        from starlite_saqlalchemy.db import engine

        while True:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
            except Exception as exc:
                logger.info("Waiting for DB: %s", exc)
                await asyncio.sleep(5)
            else:
                logger.info("DB OK!")
                break


async def _redis_ready() -> None:
    """Wait for redis to become responsive."""
    if constants.IS_REDIS_INSTALLED:
        from starlite_saqlalchemy import redis

        while True:
            try:
                await redis.client.ping()
            except Exception as exc:
                logger.info("Waiting  for Redis: %s", exc)
                await asyncio.sleep(5)
            else:
                logger.info("Redis OK!")
                break


async def before_startup_handler(_: starlite.Starlite) -> None:
    """Do things before the app starts up."""
    if settings.app.CHECK_DB_READY:
        await _db_ready()
    if settings.app.CHECK_REDIS_READY:
        await _redis_ready()
