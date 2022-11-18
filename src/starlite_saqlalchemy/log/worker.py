"""Log config and utils for the worker instance."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import structlog

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from typing import Any, TypeAlias

    from saq import Job

LOGGER = structlog.get_logger()

Context: TypeAlias = "dict[str, Any]"


async def before_process(_: Context) -> None:
    """Clear the structlog contextvars for this task."""
    structlog.contextvars.clear_contextvars()


async def after_process(ctx: Context) -> None:
    """Parse log context and log it along with the contextvars context."""
    # parse log context from `ctx`
    job: Job = ctx["job"]
    log_ctx = {k: getattr(job, k) for k in settings.log.JOB_FIELDS}
    # emit the log
    if job.error:
        level = logging.ERROR
    else:
        level = logging.INFO
    await LOGGER.alog(level, settings.log.WORKER_EVENT, **log_ctx)
