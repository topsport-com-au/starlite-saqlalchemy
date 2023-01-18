"""SAQ worker and queue."""
from __future__ import annotations

import asyncio
import dataclasses
import inspect
import logging
from functools import partial
from typing import TYPE_CHECKING, Any

import msgspec
import saq
from starlite.utils.serialization import default_serializer

from starlite_saqlalchemy import constants, redis, settings, type_encoders, utils

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection
    from signal import Signals

    from saq.types import Context

    from starlite_saqlalchemy.service import Service

__all__ = [
    "JobConfig",
    "Queue",
    "Worker",
    "create_worker_instance",
    "default_job_config_dict",
    "make_service_callback",
    "enqueue_background_task_for_service",
    "queue",
]

logger = logging.getLogger(__name__)

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


async def make_service_callback(
    _ctx: Context, *, service_type_id: str, service_method_name: str, **kwargs: Any
) -> None:
    """Make an async service callback.

    Args:
        _ctx: the SAQ context
        service_type_id: Value of `__id__` class var on service type.
        service_method_name: Method to be called on the service object.
        **kwargs: Unpacked into the service method call as keyword arguments.
    """
    service_type = constants.SERVICE_OBJECT_IDENTITY_MAP[service_type_id]
    async with service_type.new() as service_object:
        method = getattr(service_object, service_method_name)
        await method(**kwargs)


async def enqueue_background_task_for_service(
    service_obj: Service, method_name: str, job_config: JobConfig | None = None, **kwargs: Any
) -> None:
    """Enqueue an async callback for the operation and data.

    Args:
        service_obj: The Service instance that is requesting the callback.
        method_name: Method on the service object that should be called by the async worker.
        job_config: Configuration object to control the job that is enqueued.
        **kwargs: Arguments to be passed to the method when called. Must be JSON serializable.
    """
    module = inspect.getmodule(service_obj)
    if module is None:  # pragma: no cover
        logger.warning("Callback not enqueued, no module resolved for %s", service_obj)
        return
    job_config_dict: dict[str, Any]
    if job_config is None:
        job_config_dict = default_job_config_dict
    else:
        job_config_dict = utils.dataclass_as_dict_shallow(job_config, exclude_none=True)

    kwargs["service_type_id"] = service_obj.__id__
    kwargs["service_method_name"] = method_name
    job = saq.Job(
        function=make_service_callback.__qualname__,
        kwargs=kwargs,
        **job_config_dict,
    )
    await queue.enqueue(job)
