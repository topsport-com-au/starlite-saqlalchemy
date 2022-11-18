"""SAQ worker and queue."""
from __future__ import annotations

import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any

import orjson
import saq

from starlite_saqlalchemy import redis, settings

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection
    from signal import Signals

__all__ = [
    "Queue",
    "Worker",
    "create_worker_instance",
    "queue",
]


class Queue(saq.Queue):
    """Async task queue."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """[SAQ
        Queue](https://github.com/tobymao/saq/blob/master/saq/queue.py).

        Configures `orjson` for JSON serialization/deserialization if not
        otherwise configured.

        Args:
            *args: Passed through to `saq.Queue.__init__()`
            **kwargs: Passed through to `saq.Queue.__init__()`
        """
        kwargs.setdefault("name", settings.app.slug)
        kwargs.setdefault("dump", partial(orjson.dumps, default=str))
        kwargs.setdefault("load", orjson.loads)
        super().__init__(*args, **kwargs)


class Worker(saq.Worker):
    """Modify behavior of saq worker for orchestration by Starlite."""

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list[Signals] = []

    async def on_app_startup(self) -> None:  # pragma: no cover
        """Attach the worker to the running event loop."""
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())


queue = Queue(redis.client)
"""
[Queue][starlite_saqlalchemy.worker.Queue] instance instantiated with
[redis][starlite_saqlalchemy.redis.client] instance.
"""


def create_worker_instance(
    functions: Collection[Callable[..., Any] | tuple[str, Callable]],
    before_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    after_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
) -> Worker:
    """

    Args:
        functions: Functions to be called via the async workers.
        before_process: Async function called before a job processes.
        after_process: Async function called after a job processes.

    Returns:
        The worker instance, instantiated with `functions`.
    """
    return Worker(queue, functions, before_process=before_process, after_process=after_process)
