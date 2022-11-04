"""All the logging config and things are in here."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import orjson
import structlog
from starlite.config.logging import LoggingConfig

from starlite_saqlalchemy import settings

from .controller import drop_health_logs

if TYPE_CHECKING:
    from collections.abc import Sequence

    from structlog.typing import Processor

__all__ = ("default_processors", "config", "configure")

default_processors = [
    structlog.contextvars.merge_contextvars,
    drop_health_logs,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

if sys.stderr.isatty():  # pragma: no cover
    default_processors.extend([structlog.dev.ConsoleRenderer()])
else:
    default_processors.extend(
        [
            structlog.processors.format_exc_info,
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
        logger_factory=structlog.BytesLoggerFactory(),
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
        "uvicorn.error": {
            "propagate": False,
            "handlers": ["queue_listener"],
        },
        "saq": {
            "propagate": False,
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
of our dependencies are logged in a non-blocking manner.
"""
