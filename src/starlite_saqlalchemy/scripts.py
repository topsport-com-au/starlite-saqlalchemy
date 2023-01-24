"""Application startup script."""
from __future__ import annotations

from typing import Literal, TypeVar

import uvicorn

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.constants import IS_LOCAL_ENVIRONMENT


def determine_should_reload() -> bool:
    """Evaluate whether reloading should be enabled."""
    return settings.server.RELOAD if settings.server.RELOAD is not None else IS_LOCAL_ENVIRONMENT


def determine_reload_dirs(should_reload: bool) -> list[str] | None:
    """

    Args:
        should_reload: is reloading enabled?

    Returns:
        List of directories to watch, or `None` if reloading disabled.
    """
    return settings.server.RELOAD_DIRS if should_reload else None


T = TypeVar("T")


def run_app(
    app: str | None = None,
    factory: bool | None = None,
    host: str | None = None,
    loop: Literal["none", "auto", "asyncio", "uvloop"] | None = None,
    port: int | None = None,
    reload: bool | None = None,
    reload_dirs: list[str] | None = None,
    timeout_keep_alive: int | None = None,
) -> None:
    """Run the application with config via environment."""
    should_reload = _not_none(reload, determine_should_reload())
    reload_dirs = _not_none(reload_dirs, determine_reload_dirs(should_reload))
    uvicorn.run(
        app=_not_none(app, settings.server.APP_LOC),
        factory=_not_none(factory, settings.server.APP_LOC_IS_FACTORY),
        host=_not_none(host, settings.server.HOST),
        loop=_not_none(loop, "auto"),
        port=_not_none(port, settings.server.PORT),
        reload=should_reload,
        reload_dirs=reload_dirs,
        timeout_keep_alive=_not_none(timeout_keep_alive, settings.server.KEEPALIVE),
    )


def _not_none(maybe_none: T | None, fallback: T) -> T:
    return maybe_none if maybe_none is not None else fallback
