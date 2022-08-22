import logging
from collections import abc
from functools import partial
from typing import TYPE_CHECKING, Any

import orjson
import saq

from .db import async_session_factory
from .redis import redis

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession  # noqa:F401

__all__ = [
    "Queue",
    "Worker",
    "WorkerFunction",
    "queue",
]

logger = logging.getLogger(__name__)


WorkerFunction = abc.Callable[..., abc.Awaitable[Any]]


class Queue(saq.Queue):
    """
    [SAQ Queue](https://github.com/tobymao/saq/blob/master/saq/queue.py)

    Configures `orjson` for JSON serialization/deserialization if not otherwise configured.

    Parameters
    ----------
    *args : Any
        Passed through to `saq.Queue.__init__()`
    **kwargs : Any
        Passed through to `saq.Queue.__init__()`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("dump", partial(orjson.dumps, default=str))
        kwargs.setdefault("load", orjson.loads)
        super().__init__(*args, **kwargs)


async def _before_process(ctx: dict) -> None:
    ctx["session"] = async_session_factory()
    logger.debug("'session' to `ctx`: `%s`", ctx)


async def _after_process(ctx: dict) -> None:
    session = ctx.get("session")
    if session:
        logger.debug("closing session: `%s`", session)
        await session.close()
    else:
        logger.debug("no `'session'` in `ctx`: `%s`", ctx)


def get_session_from_context(ctx: dict) -> "AsyncSession":
    return ctx["session"]  # type:ignore[no-any-return]


class Worker(saq.Worker):
    """
    [SAQ worker](https://github.com/tobymao/saq/blob/master/saq/worker.py).

    We set [AsyncScopedSession.remove()][starlite_lib.db.AsyncScopedSession] to
    `Worker.after_process` if it is not otherwise provided. If passing a different async function
    for that parameter the caller should take responsibility to ensure that the
    [`async_scoped_session.remove()`][sqlalchemy.ext.asyncio.async_scoped_session.remove] method
    is called on task completion.

    Parameters
    ----------
    *args : Any
        Passed straight through to `saq.Worker.__init__()`.
    **kwargs : Any
        Passed straight through to `saq.Worker.__init__()`.
    """

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list[str] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("before_process", _before_process)
        kwargs.setdefault("after_process", _after_process)
        super().__init__(*args, **kwargs)


queue = Queue(redis)
"""
[Queue][starlite_lib.worker.Queue] instance instantiated with [redis][starlite_lib.redis.redis] 
instance.
"""
