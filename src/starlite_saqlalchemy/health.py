import contextlib

from sqlalchemy.ext.asyncio import AsyncSession
from starlite import get
from starlite.exceptions import ServiceUnavailableException

from . import settings
from .repository.sqlalchemy import SQLAlchemyRepository
from .settings import AppSettings


class HealthCheckFailure(ServiceUnavailableException):
    """Raise for health check failure."""


@get(path=settings.api.HEALTH_PATH, cache=False, tags=["Misc"])
async def health_check(db_session: AsyncSession) -> AppSettings:
    """Check database available and returns app config info."""
    with contextlib.suppress(Exception):
        if await SQLAlchemyRepository.check_health(db_session):
            return settings.app
    raise HealthCheckFailure("DB not ready.")
