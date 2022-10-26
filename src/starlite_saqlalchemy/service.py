"""A generic service object implementation.

Service object is generic on the domain model type, which should be a
SQLAlchemy model.
"""

import importlib
import inspect
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from . import dto
from .repository.sqlalchemy import ModelT
from .sqlalchemy_plugin import async_session_factory
from .worker import queue

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.ext.asyncio import AsyncSession

    from .repository.abc import AbstractRepository
    from .repository.types import FilterTypes


logger = logging.getLogger(__name__)

ServiceT = TypeVar("ServiceT", bound="Service")


class ServiceException(Exception):
    """Base class for `Service` related exceptions."""


class UnauthorizedException(ServiceException):
    """A user tried to do something they shouldn't have."""


class Operation(str, Enum):
    """Operation type markers sent with callbacks."""

    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


class Service(Generic[ModelT]):
    """Generic Service object.

    Args:
        repository: Instance conforming to `AbstractRepository` interface.
    """

    _INTERNAL_DTO_CACHE: dict[type["Service"], type["BaseModel"]] = {}

    repository_type: type["AbstractRepository[ModelT]"]

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Create and cache a DTO instance that is internal use only.

        note:
            This pattern could be changed to on first access, rather than at compile time.
        """
        super().__init_subclass__(*args, **kwargs)
        model_type = cls.repository_type.model_type
        cls._INTERNAL_DTO_CACHE[cls] = dto.factory(
            f"__{model_type.__tablename__}DTO", model_type, dto.Purpose.READ
        )

    def __init__(self, session: "AsyncSession") -> None:
        self.repository = self.repository_type(session)

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
        data = await self.repository.add(data)
        await self.enqueue_callback(Operation.CREATE, data)
        return data

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
        data = await self.repository.update(data)
        await self.enqueue_callback(Operation.UPDATE, data)
        return data

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
        data = await self.repository.upsert(data)
        await self.enqueue_callback(Operation.UPDATE, data)
        return data

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
        data = await self.repository.delete(id_)
        await self.enqueue_callback(Operation.DELETE, data)
        return data

    async def enqueue_callback(self, operation: Operation, data: ModelT) -> None:
        """Enqueue an async callback for the operation and data.

        Args:
            operation: Operation performed on data.
            data: The data for the operation.
        """
        module = inspect.getmodule(self)
        if module is None:
            logger.warning("Callback not enqueued, no module resolved for %s", self)
            return
        await queue.enqueue(
            make_service_callback.__qualname__,
            service_module_name=module.__name__,
            service_type_fqdn=type(self).__qualname__,
            operation=operation,
            raw_obj=self._get_model_dto().from_orm(data).dict(),
        )

    async def receive_callback(self, operation: Operation, raw_obj: dict[str, Any]) -> None:
        """Method called by the async workers.

        Do what you want in here but remember not to block the loop.

        Args:
            operation: Operation performed on the object.
            raw_obj: Raw representation of the object.
        """
        dto_parsed_obj = self._get_model_dto().parse_obj(raw_obj)
        model_instance = self.repository_type.model_type(**dto_parsed_obj.dict())
        logger.info("Callback executed for %s: %s", operation, model_instance)

    @classmethod
    def _get_model_dto(cls) -> type["BaseModel"]:
        """DTO for model cached globally on first access.

        Returns:
            Pydantic model instance used for internal deserialization.
        """
        return cls._INTERNAL_DTO_CACHE[cls]


async def make_service_callback(
    _ctx: dict,
    *,
    service_module_name: str,
    service_type_fqdn: str,
    operation: Operation,
    raw_obj: dict[str, Any],
) -> None:
    """Function that makes the async service callbacks.

    Args:
        _ctx: the SAQ context
        service_module_name: Module of service type to instantiate.
        service_type_fqdn: Reference to service type in module.
        operation: Operation performed on the instance.
        raw_obj: Data received from the work queue.
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
    await service_object.receive_callback(operation, raw_obj=raw_obj)
