"""Health check handler for the application.

Returns the app settings as details if successful, otherwise a 503.
"""
from __future__ import annotations

import contextlib

from sqlalchemy.ext.asyncio import AsyncSession
from starlite import get
from starlite.exceptions import ServiceUnavailableException

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository
from starlite_saqlalchemy.settings import AppSettings


class HealthCheckFailure(ServiceUnavailableException):
    """Raise for health check failure."""


@get(path=settings.api.HEALTH_PATH, tags=["Misc"])
async def health_check(db_session: AsyncSession) -> AppSettings:
    """Check database available and returns app config info."""
    with contextlib.suppress(Exception):
        if await SQLAlchemyRepository.check_health(db_session):
            return settings.app
    raise HealthCheckFailure("DB not ready.")
