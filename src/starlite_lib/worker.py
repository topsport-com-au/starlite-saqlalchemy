from collections import abc
from functools import partial
from typing import Any

import orjson
import saq

from .db import AsyncScopedSession
from .redis import redis

__all__ = [
    "Queue",
    "Worker",
    "WorkerFunction",
    "queue",
]


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


async def _after_process(_: Any) -> None:
    await AsyncScopedSession.remove()


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
        kwargs.setdefault("after_process", _after_process)
        super().__init__(*args, **kwargs)


queue = Queue(redis)
"""
[Queue][starlite_lib.worker.Queue] instance instantiated with [redis][starlite_lib.redis.redis] 
instance.
"""
