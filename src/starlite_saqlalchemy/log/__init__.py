"""All the logging config and things are in here."""

from __future__ import annotations

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

if sys.stderr.isatty() or "pytest" in sys.modules:  # pragma: no cover
    LoggerFactory: Any = structlog.WriteLoggerFactory
    default_processors.extend([structlog.dev.ConsoleRenderer()])
else:  # pragma: no cover
    LoggerFactory = structlog.BytesLoggerFactory
    default_processors.extend(
        [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(serializer=orjson.dumps),
        ]
    )


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
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.LEVEL),
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
            "level": settings.log.UVICORN_ACCESS_LEVEL,
            "handlers": ["queue_listener"],
        },
        "uvicorn.error": {
            "propagate": False,
            "level": settings.log.UVICORN_ERROR_LEVEL,
            "handlers": ["queue_listener"],
        },
        "saq": {
            "propagate": False,
            "level": settings.log.SAQ_LEVEL,
            "handlers": ["queue_listener"],
        },
        "sqlalchemy.engine": {
            "propagate": False,
            "level": settings.log.SQLALCHEMY_LEVEL,
            "handlers": ["queue_listener"],
        },
    },
)
"""Pre-configured log config for application deps.

While we use structlog for internal app logging, we still want to ensure that logs emitted by any
of our dependencies are handled in a non-blocking manner.
"""
