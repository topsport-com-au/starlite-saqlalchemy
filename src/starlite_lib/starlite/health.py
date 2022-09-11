from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlite import get

from starlite_lib.config import AppSettings, api_settings, app_settings


@get(path=api_settings.HEALTH_PATH, cache=False, tags=["Misc"])
async def health_check(session: AsyncSession) -> AppSettings:
    """Check database available and returns app config info."""
    assert (await session.execute(text("SELECT 1"))).scalar_one() == 1
    return app_settings
