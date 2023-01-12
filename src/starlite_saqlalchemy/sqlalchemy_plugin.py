"""Database connectivity and transaction management for the application."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.plugins.sql_alchemy.config import (
    SESSION_SCOPE_KEY,
    SESSION_TERMINUS_ASGI_EVENTS,
)

from starlite_saqlalchemy import db, settings
from starlite_saqlalchemy.health import AbstractHealthCheck

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from starlite.datastructures.state import State
    from starlite.types import Message, Scope

__all__ = ["config", "plugin"]


async def before_send_handler(message: "Message", _: "State", scope: "Scope") -> None:
    """Inspect status of response and commit, or rolls back.

    Args:
        message: ASGI message
        _:
        scope: ASGI scope
    """
    session = cast("AsyncSession | None", scope.get(SESSION_SCOPE_KEY))
    try:
        if session is not None and message["type"] == "http.response.start":
            if 200 <= message["status"] < 300:
                await session.commit()
            else:
                await session.rollback()
    finally:
        if session is not None and message["type"] in SESSION_TERMINUS_ASGI_EVENTS:
            await session.close()
            del scope[SESSION_SCOPE_KEY]  # type:ignore[misc]


class SQLAlchemyHealthCheck(AbstractHealthCheck):
    """SQLAlchemy health check."""

    name: str = "db"

    def __init__(self) -> None:
        self.engine = create_async_engine(
            settings.db.URL, logging_name="starlite_saqlalchemy.health"
        )
        self.session_maker = async_sessionmaker(bind=self.engine)

    async def ready(self) -> bool:
        """Perform a health check on the database.

        Returns:
            `True` if healthy.
        """
        async with self.session_maker() as session:
            return (  # type:ignore[no-any-return]  # pragma: no cover
                await session.execute(text("SELECT 1"))
            ).scalar_one() == 1


config = SQLAlchemyConfig(
    before_send_handler=before_send_handler,
    dependency_key=settings.api.DB_SESSION_DEPENDENCY_KEY,
    engine_instance=db.engine,
    session_maker_instance=db.async_session_factory,
)

plugin = SQLAlchemyPlugin(config=config)
