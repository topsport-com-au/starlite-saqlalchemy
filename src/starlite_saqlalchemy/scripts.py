"""Application startup script."""
from __future__ import annotations

import asyncio
import signal
from typing import TYPE_CHECKING, Any

import uvicorn
import uvloop

from starlite_saqlalchemy import log, settings
from starlite_saqlalchemy.constants import IS_LOCAL_ENVIRONMENT
from starlite_saqlalchemy.worker import (
    create_worker_instance,
    make_service_callback,
    queue,
)


def determine_should_reload() -> bool:
    """Evaluate whether reloading should be enabled."""
    return settings.server.RELOAD if settings.server.RELOAD is not None else IS_LOCAL_ENVIRONMENT


def determine_reload_dirs(should_reload: bool) -> list[str] | None:
    """Determine reload directories.

    Args:
        should_reload: is reloading enabled?

    Returns:
        List of directories to watch, or `None` if reloading disabled.
    """
    return settings.server.RELOAD_DIRS if should_reload else None


def run_app() -> None:
    """Run the application with config via environment."""
    should_reload = determine_should_reload()
    reload_dirs = determine_reload_dirs(should_reload)
    uvicorn.run(
        app=settings.server.APP_LOC,
        factory=settings.server.APP_LOC_IS_FACTORY,
        host=settings.server.HOST,
        loop="auto",
        port=settings.server.PORT,
        reload=should_reload,
        reload_dirs=reload_dirs,
        timeout_keep_alive=settings.server.KEEPALIVE,
    )


def run_worker() -> None:
    """Run a worker."""
    log.config.configure()
    worker_kwargs: dict[str, Any] = {
        "functions": [(make_service_callback.__qualname__, make_service_callback)],
    }
    worker_kwargs["before_process"] = log.worker.before_process
    worker_kwargs["after_process"] = log.worker.after_process
    worker_instance = create_worker_instance(**worker_kwargs)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.new_event_loop()
    for signals in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            signals,
            lambda: asyncio.create_task(worker_instance.stop()),
        )

    if settings.worker.WEB_ENABLED:
        import aiohttp.web  # pyright:ignore[reportMissingImports] # pylint: disable=import-outside-toplevel,import-error
        from saq.web import create_app  # pylint: disable=import-outside-toplevel

        if TYPE_CHECKING:
            from aiohttp.web_app import (  # pyright:ignore[reportMissingImports] # pylint: disable=import-outside-toplevel
                Application,
            )

        async def shutdown(_app: Application) -> None:
            await worker_instance.stop()

        app = create_app([queue])
        app.on_shutdown.append(shutdown)

        loop.create_task(worker_instance.start())
        aiohttp.web.run_app(app, port=settings.worker.WEB_PORT, loop=loop)
    else:
        loop.run_until_complete(worker_instance.start())
