"""Tests for the sqlalchemy plugin."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from starlite.plugins.sql_alchemy.config import SESSION_SCOPE_KEY

from starlite_saqlalchemy import sqlalchemy_plugin

if TYPE_CHECKING:
    from starlite import Starlite
    from starlite.types import HTTPResponseStartEvent, HTTPScope


async def test_before_send_handler_success_response(
    app: Starlite, http_response_start: HTTPResponseStartEvent, http_scope: HTTPScope
) -> None:
    """Test that the session is committed given a success response."""
    mock_session = MagicMock(spec=AsyncSession)
    http_scope[SESSION_SCOPE_KEY] = mock_session  # type:ignore[literal-required]
    http_response_start["status"] = random.randint(200, 299)
    await sqlalchemy_plugin.before_send_handler(http_response_start, app.state, http_scope)
    mock_session.commit.assert_awaited_once()


async def test_before_send_handler_error_response(
    app: Starlite, http_response_start: HTTPResponseStartEvent, http_scope: HTTPScope
) -> None:
    """Test that the session is committed given a success response."""
    mock_session = MagicMock(spec=AsyncSession)
    http_scope[SESSION_SCOPE_KEY] = mock_session  # type:ignore[literal-required]
    http_response_start["status"] = random.randint(300, 599)
    await sqlalchemy_plugin.before_send_handler(http_response_start, app.state, http_scope)
    mock_session.rollback.assert_awaited_once()
