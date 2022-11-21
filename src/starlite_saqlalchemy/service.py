"""A generic service object implementation.

Service object is generic on the domain model type, which should be a
SQLAlchemy model.
"""
from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from starlite_saqlalchemy.db import async_session_factory
from starlite_saqlalchemy.repository.types import ModelT
from starlite_saqlalchemy.worker import queue

if TYPE_CHECKING:
    from saq.types import Context

    from starlite_saqlalchemy.repository.abc import AbstractRepository
    from starlite_saqlalchemy.repository.types import FilterTypes


logger = logging.getLogger(__name__)

ServiceT = TypeVar("ServiceT", bound="Service")

service_object_identity_map: dict[str, type[Service]] = {}


class ServiceException(Exception):
    """Base class for `Service` related exceptions."""


class UnauthorizedException(ServiceException):
    """A user tried to do something they shouldn't have."""


class Service(Generic[ModelT]):
    """Generic Service object."""

    __id__: ClassVar[str]
    repository_type: type[AbstractRepository[ModelT]]

    def __init__(self, **repo_kwargs: Any) -> None:
        """Configure the service object.

        Args:
            **repo_kwargs: passed as keyword args to repo instantiation.
        """
        self.repository = self.repository_type(**repo_kwargs)

    def __init_subclass__(cls, *_: Any, **__: Any) -> None:
        """Map the service object to a unique identifier.

        Important that the id is deterministic across running
        application instances, e.g., using something like `hash()` or
        `id()` won't work as those would be different on different
        instances of the running application. So we use the full import
        path to the object.
        """
        cls.__id__ = f"{cls.__module__}.{cls.__name__}"
        service_object_identity_map[cls.__id__] = cls

    async def create(self, data: ModelT) -> ModelT:
        """Wrap repository instance creation.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return await self.repository.add(data)

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[ModelT]:
        """Wrap repository scalars operation.

        Args:
            *filters: Collection route filters.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        return await self.repository.list(*filters, **kwargs)

    async def update(self, id_: Any, data: ModelT) -> ModelT:
        """Wrap repository update operation.

        Args:
            id_: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        self.repository.set_id_attribute_value(id_, data)
        return await self.repository.update(data)

    async def upsert(self, id_: Any, data: ModelT) -> ModelT:
        """Wrap repository upsert operation.

        Args:
            id_: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        self.repository.set_id_attribute_value(id_, data)
        return await self.repository.upsert(data)

    async def get(self, id_: Any) -> ModelT:
        """Wrap repository scalar operation.

        Args:
            id_: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `id_`.
        """
        return await self.repository.get(id_)

    async def delete(self, id_: Any) -> ModelT:
        """Wrap repository delete operation.

        Args:
            id_: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        return await self.repository.delete(id_)

    async def enqueue_background_task(self, method_name: str, **kwargs: Any) -> None:
        """Enqueue an async callback for the operation and data.

        Args:
            method_name: Method on the service object that should be called by the async worker.
            **kwargs: Arguments to be passed to the method when called. Must be JSON serializable.
        """
        module = inspect.getmodule(self)
        if module is None:  # pragma: no cover
            logger.warning("Callback not enqueued, no module resolved for %s", self)
            return
        await queue.enqueue(
            make_service_callback.__qualname__,
            service_type_id=self.__id__,
            service_method_name=method_name,
            **kwargs,
        )


async def make_service_callback(
    _ctx: Context,
    *,
    service_type_id: str,
    service_method_name: str,
    **kwargs: Any,
) -> None:
    """Make an async service callback.

    Args:
        _ctx: the SAQ context
        service_type_id: Value of `__id__` class var on service type.
        service_method_name: Method to be called on the service object.
        **kwargs: Unpacked into the service method call as keyword arguments.
    """
    service_type = service_object_identity_map[service_type_id]
    async with async_session_factory() as session:
        service_object: Service = service_type(session=session)
    method = getattr(service_object, service_method_name)
    await method(**kwargs)
