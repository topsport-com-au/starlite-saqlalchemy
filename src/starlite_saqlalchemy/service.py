"""A generic service object implementation.

Service object is generic on the domain model type, which should be a
SQLAlchemy model.
"""
from __future__ import annotations

import importlib
import inspect
import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from starlite_saqlalchemy.repository.sqlalchemy import ModelT
from starlite_saqlalchemy.sqlalchemy_plugin import async_session_factory
from starlite_saqlalchemy.worker import queue

if TYPE_CHECKING:
    from starlite_saqlalchemy.repository.abc import AbstractRepository
    from starlite_saqlalchemy.repository.types import FilterTypes


logger = logging.getLogger(__name__)

ServiceT = TypeVar("ServiceT", bound="Service")
Context = dict[str, Any]


class ServiceException(Exception):
    """Base class for `Service` related exceptions."""


class UnauthorizedException(ServiceException):
    """A user tried to do something they shouldn't have."""


class Service(Generic[ModelT]):
    """Generic Service object."""

    repository_type: type[AbstractRepository[ModelT]]

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: AbstractRepository[ModelT] = self.repository_type(**repo_kwargs)

    # noinspection PyMethodMayBeStatic
    async def authorize_create(self, data: ModelT) -> ModelT:
        """Control resource creation.

        Can use `self.user` here.

        Args:
            data: The object to be created.

        Returns:
            The object with restricted attribute values removed.
        """
        return data

    async def create(self, data: ModelT) -> ModelT:
        """Wraps repository instance creation.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        data = await self.authorize_create(data)
        return await self.repository.add(data)

    # noinspection PyMethodMayBeStatic
    async def authorize_list(self) -> None:
        """Authorize collection access."""

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[ModelT]:
        """Wraps repository scalars operation.

        Args:
            *filters: Collection route filters.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        await self.authorize_list()
        return await self.repository.list(*filters, **kwargs)

    async def authorize_update(self, id_: Any, data: ModelT) -> ModelT:
        """Authorize update of item.

        Args:
            id_: Identifier of the object to be updated.
            data: The object to be updated.

        Returns:
            ModelT
        """
        self.repository.set_id_attribute_value(id_, data)
        return data

    async def update(self, id_: Any, data: ModelT) -> ModelT:
        """Wraps repository update operation.

        Args:
            id_: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        data = await self.authorize_update(id_, data)
        return await self.repository.update(data)

    async def authorize_upsert(self, id_: Any, data: ModelT) -> ModelT:
        """Authorize upsert of item.

        Args:
            id_: The identifier of the resource to upsert.
            data: The object to be updated.

        Returns:
            ModelT
        """
        self.repository.set_id_attribute_value(id_, data)
        return data

    async def upsert(self, id_: Any, data: ModelT) -> ModelT:
        """Wraps repository upsert operation.

        Args:
            id_: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        data = await self.authorize_upsert(id_, data)
        return await self.repository.upsert(data)

    async def authorize_get(self, id_: Any) -> None:
        """Authorize get of item.

        Args:
            id_: Identifier of item to be retrieved.
        """

    async def get(self, id_: Any) -> ModelT:
        """Wraps repository scalar operation.

        Args:
            id_: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `id_`.
        """
        await self.authorize_get(id_)
        return await self.repository.get(id_)

    async def authorize_delete(self, id_: Any) -> None:
        """Authorize delete of item.

        Args:
            id_: Identifier of item to be retrieved.
        """

    async def delete(self, id_: Any) -> ModelT:
        """Wraps repository delete operation.

        Args:
            id_: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        await self.authorize_delete(id_)
        return await self.repository.delete(id_)

    async def enqueue_background_task(self, method_name: str, **kwargs: Any) -> None:
        """Enqueue an async callback for the operation and data.

        Args:
            method_name: Method on the service object that should be called by the async worker.
            **kwargs: Arguments to be passed to the method when called.

                Note:
                    Must be JSON serializable.
        """
        module = inspect.getmodule(self)
        if module is None:
            logger.warning("Callback not enqueued, no module resolved for %s", self)
            return
        await queue.enqueue(
            make_service_callback.__qualname__,
            service_module_name=module.__name__,
            service_type_fqdn=type(self).__qualname__,
            service_method_name=method_name,
            **kwargs,
        )


async def make_service_callback(
    _ctx: Context,
    *,
    service_module_name: str,
    service_type_fqdn: str,
    service_method_name: str,
    **kwargs: Any,
) -> None:
    """Function that makes the async service callbacks.

    Args:
        _ctx: the SAQ context
        service_module_name: Module of service type to instantiate.
        service_type_fqdn: Reference to service type in module.
        service_method_name: Method to be called on the service object.
        **kwargs: Unpacked into the service method call as keyword arguments.
    """
    service_module = importlib.import_module(service_module_name)
    for name in service_type_fqdn.split("."):
        obj_ = getattr(service_module, name)
        if issubclass(obj_, Service):
            service_type = obj_
            break
    else:
        raise RuntimeError("Couldn't find a service type with given module and fqdn")
    async with async_session_factory() as session:
        service_object: Service = service_type(session=session)
    method = getattr(service_object, service_method_name)
    await method(**kwargs)
