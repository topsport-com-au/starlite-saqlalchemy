"""Database connectivity and transaction management for the application."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.plugins.sql_alchemy.config import (
    SESSION_SCOPE_KEY,
    SESSION_TERMINUS_ASGI_EVENTS,
)

from starlite_saqlalchemy import db, settings

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


config = SQLAlchemyConfig(
    before_send_handler=before_send_handler,
    dependency_key=settings.api.DB_SESSION_DEPENDENCY_KEY,
    engine_instance=db.engine,
    session_maker_instance=db.async_session_factory,
)

plugin = SQLAlchemyPlugin(config=config)
