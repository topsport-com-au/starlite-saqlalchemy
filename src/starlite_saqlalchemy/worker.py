"""SAQ worker and queue."""
import asyncio
from collections import abc
from functools import partial
from typing import TYPE_CHECKING, Any

import orjson
import saq

from starlite_saqlalchemy import redis

if TYPE_CHECKING:
    from signal import Signals

__all__ = [
    "Queue",
    "Worker",
    "WorkerFunction",
    "create_worker_instance",
    "queue",
]

WorkerFunction = abc.Callable[..., abc.Awaitable[Any]]


class Queue(saq.Queue):
    """[SAQ Queue](https://github.com/tobymao/saq/blob/master/saq/queue.py).

    Configures `orjson` for JSON serialization/deserialization if not otherwise configured.

    Args:
        *args: Passed through to `saq.Queue.__init__()`
        **kwargs: Passed through to `saq.Queue.__init__()`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("dump", partial(orjson.dumps, default=str))
        kwargs.setdefault("load", orjson.loads)
        super().__init__(*args, **kwargs)


class Worker(saq.Worker):
    """Modify behavior of saq worker for orchestration by Starlite."""

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list["Signals"] = []

    async def on_app_startup(self) -> None:
        """Attach the worker to the running event loop."""
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())


queue = Queue(redis.client)
"""
[Queue][starlite_saqlalchemy.worker.Queue] instance instantiated with
[redis][starlite_saqlalchemy.redis.client] instance.
"""


def create_worker_instance(
    functions: abc.Collection[WorkerFunction | tuple[str, WorkerFunction]]
) -> Worker:
    """

    Args:
        functions: Functions to be called via the async workers.

    Returns:
        The worker instance, instantiated with `functions`.
    """
    return Worker(queue, functions)
