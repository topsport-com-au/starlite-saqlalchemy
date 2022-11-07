"""All the logging config and things are in here."""

from __future__ import annotations

import asyncio
import contextvars
import logging
import sys
from typing import TYPE_CHECKING

import orjson
import structlog
from starlite.config.logging import LoggingConfig

from starlite_saqlalchemy import settings

from . import controller, worker

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from structlog.types import Processor

__all__ = (
    "default_processors",
    "config",
    "configure",
    "controller",
    "worker",
)

default_processors = [
    structlog.contextvars.merge_contextvars,
    controller.drop_health_logs,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

if sys.stderr.isatty():  # pragma: no cover
    LoggerFactory: Any = structlog.WriteLoggerFactory
    default_processors.extend([structlog.dev.ConsoleRenderer()])
else:
    LoggerFactory = structlog.BytesLoggerFactory
    default_processors.extend(
        [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(serializer=orjson.dumps),
        ]
    )


def _make_filtering_bound_logger(min_level: int) -> type[structlog.types.FilteringBoundLogger]:
    """Wraps structlog's `FilteringBoundLogger` to add the `alog()` method,
    which is in structlog's main branch, but not yet released.

    Args:
        min_level: Log level as an integer.

    Returns:
        Structlog's `FilteringBoundLogger` with an `alog()` method that does its work off the event
        loop.
    """
    filtering_bound_logger = structlog.make_filtering_bound_logger(min_level=min_level)

    # pylint: disable=too-few-public-methods
    class _WrappedFilteringBoundLogger(filtering_bound_logger):  # type:ignore[misc,valid-type]
        async def alog(self: Any, level: int, event: str, *args: Any, **kw: Any) -> Any:
            """This method will exist in the next release of structlog."""
            if level < min_level:
                return None
            # pylint: disable=protected-access
            name = structlog._log_levels._LEVEL_TO_NAME[level]  # pyright: ignore

            ctx = contextvars.copy_context()
            return await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: ctx.run(
                    lambda: self._proxy_to_logger(  # type:ignore[no-any-return]
                        name, event % args, **kw
                    )
                ),
            )

    return _WrappedFilteringBoundLogger


def configure(processors: Sequence[Processor]) -> None:
    """Call to configure `structlog` on app startup.

    The calls to `structlog.get_logger()` in `controller.py` and
    `worker.py` return proxies to the logger that is eventually called
    after this configurator function has been called. Therefore, nothing
    should try to log via structlog before this is called.
    """
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=LoggerFactory(),
        processors=processors,
        wrapper_class=_make_filtering_bound_logger(settings.log.LEVEL),
    )


config = LoggingConfig(
    root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
    formatters={
        "standard": {
            "format": (
                "%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() "
                "L%(lineno)-4d %(message)s"
            )
        }
    },
    loggers={
        "uvicorn.access": {
            "propagate": False,
            "level": logging.WARNING,
            "handlers": ["queue_listener"],
        },
        "uvicorn.error": {
            "propagate": False,
            "level": logging.WARNING,
            "handlers": ["queue_listener"],
        },
        "saq": {
            "propagate": False,
            "level": logging.WARNING,
            "handlers": ["queue_listener"],
        },
        "sqlalchemy.engine": {
            "propagate": False,
            "handlers": ["queue_listener"],
        },
    },
)
"""Pre-configured log config for application deps.

While we use structlog for internal app logging, we still want to ensure that logs emitted by any
of our dependencies are handled in a non-blocking manner.
"""
