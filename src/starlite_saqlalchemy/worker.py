"""SAQ worker and queue."""
from __future__ import annotations

import asyncio
import dataclasses
from functools import partial
from typing import TYPE_CHECKING, Any

import msgspec
import saq
from starlite.utils.serialization import default_serializer

from starlite_saqlalchemy import redis, settings, type_encoders, utils

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection
    from signal import Signals

__all__ = [
    "JobConfig",
    "Queue",
    "Worker",
    "create_worker_instance",
    "default_job_config_dict",
    "queue",
]

encoder = msgspec.json.Encoder(
    enc_hook=partial(default_serializer, type_encoders=type_encoders.type_encoders_map)
)


class Queue(saq.Queue):
    """Async task queue."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create an SAQ Queue.

        See: https://github.com/tobymao/saq/blob/master/saq/queue.py

        Names the queue per the application slug - namespaces SAQ's redis keys to the app.

        Configures `msgspec` for JSON serialization/deserialization if not
        otherwise configured.

        Args:
            *args: Passed through to `saq.Queue.__init__()`
            **kwargs: Passed through to `saq.Queue.__init__()`
        """
        kwargs.setdefault("name", "background-worker")
        kwargs.setdefault("dump", encoder.encode)
        kwargs.setdefault("load", msgspec.json.decode)
        super().__init__(*args, **kwargs)

    def namespace(self, key: str) -> str:
        """Namespace for the Queue.

        Args:
            key (str): The unique key to use for the namespace.

        Returns:
            str: The worker namespace
        """
        return f"{settings.app.slug}:{self.name}:{key}"


class Worker(saq.Worker):
    """Modify behavior of saq worker for orchestration by Starlite."""

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list[Signals] = []

    async def on_app_startup(self) -> None:  # pragma: no cover
        """Attach the worker to the running event loop."""
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())


queue = Queue(redis.client)
"""Async worker queue.

[Queue][starlite_saqlalchemy.worker.Queue] instance instantiated with
[redis][starlite_saqlalchemy.redis.client] instance.
"""


@dataclasses.dataclass()
class JobConfig:
    """Configure a Job.

    Used to configure jobs enqueued via
    `Service.enqueue_background_task()`
    """

    # pylint:disable=too-many-instance-attributes

    queue: Queue = queue
    """Queue associated with the job."""
    key: str | None = None
    """Pass in to control duplicate jobs."""
    timeout: int = settings.worker.JOB_TIMEOUT
    """Max time a job can run for, in seconds.

    Set to `0` for no timeout.
    """
    heartbeat: int = settings.worker.JOB_HEARTBEAT
    """Max time a job can survive without emitting a heartbeat. `0` to disable.

    `job.update()` will trigger a heartbeat.
    """
    retries: int = settings.worker.JOB_RETRIES
    """Max attempts for any job."""
    ttl: int = settings.worker.JOB_TTL
    """Lifetime of available job information, in seconds.

    0: indefinite
    -1: disabled (no info retained)
    """
    retry_delay: float = settings.worker.JOB_TTL
    """Seconds to delay before retrying a job."""
    retry_backoff: bool | float = settings.worker.JOB_RETRY_BACKOFF
    """If true, use exponential backoff for retry delays.

    - The first retry will have whatever retry_delay is.
    - The second retry will have retry_delay*2. The third retry will have retry_delay*4. And so on.
    - This always includes jitter, where the final retry delay is a random number between 0 and the calculated retry delay.
    - If retry_backoff is set to a number, that number is the maximum retry delay, in seconds."
    """


default_job_config_dict = utils.dataclass_as_dict_shallow(JobConfig(), exclude_none=True)


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
