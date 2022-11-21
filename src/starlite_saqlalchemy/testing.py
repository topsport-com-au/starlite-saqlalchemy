"""A repository implementation for tests.

Uses a `dict` for storage.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import uuid4

from starlite_saqlalchemy.db.orm import Base
from starlite_saqlalchemy.repository.abc import AbstractRepository
from starlite_saqlalchemy.repository.exceptions import RepositoryConflictException

if TYPE_CHECKING:
    from collections import abc

    from starlite_saqlalchemy.repository.types import FilterTypes

BaseT = TypeVar("BaseT", bound=Base)


class GenericMockRepository(AbstractRepository[BaseT], Generic[BaseT]):
    """A repository implementation for tests.

    Uses a `dict` for storage.
    """

    collection: abc.MutableMapping[abc.Hashable, BaseT] = {}

    def __init__(self, id_factory: abc.Callable[[], Any] = uuid4, **_: Any) -> None:
        super().__init__()
        self._id_factory = id_factory

    def _find_or_raise_not_found(self, id_: Any) -> BaseT:
        return self.check_not_found(self.collection.get(id_))

    async def add(self, data: BaseT, _allow_id: bool = False) -> BaseT:
        """Add `data` to the collection.

        Args:
            data: Instance to be added to the collection.

        Returns:
            The added instance.
        """
        if _allow_id is False and self.get_id_attribute_value(data) is not None:
            raise RepositoryConflictException("`add()` received identified item.")
        now = datetime.now()
        data.updated = data.created = now
        if _allow_id is False:
            id_ = self._id_factory()
            self.set_id_attribute_value(id_, data)
        self.collection[data.id] = data
        return data

    async def delete(self, id_: Any) -> BaseT:
        """Delete instance identified by `id_`.

        Args:
            id_: Identifier of instance to be deleted.

        Returns:
            The deleted instance.

        Raises:
            RepositoryNotFoundException: If no instance found identified by `id_`.
        """
        try:
            return self._find_or_raise_not_found(id_)
        finally:
            del self.collection[id_]

    async def get(self, id_: Any) -> BaseT:
        """Get instance identified by `id_`.

        Args:
            id_: Identifier of the instance to be retrieved.

        Returns:
            The retrieved instance.

        Raises:
            RepositoryNotFoundException: If no instance found identified by `id_`.
        """
        return self._find_or_raise_not_found(id_)

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[BaseT]:
        """Get a list of instances, optionally filtered.

        Args:
            *filters: Types for specific filtering operations.
            **kwargs: Instance attribute value filters.

        Returns:
            The list of instances, after filtering applied.
        """
        return list(self.collection.values())

    async def update(self, data: BaseT) -> BaseT:
        """Update instance with the attribute values present on `data`.

        Args:
            data: An instance that should have a value for `self.id_attribute` that exists in the
                collection.

        Returns:
            The updated instance.

        Raises:
            RepositoryNotFoundException: If no instance found with same identifier as `data`.
        """
        item = self._find_or_raise_not_found(self.get_id_attribute_value(data))
        # should never be modifiable
        data.updated = datetime.now()
        for key, val in data.__dict__.items():
            if key.startswith("_"):
                continue
            setattr(item, key, val)
        return item

    async def upsert(self, data: BaseT) -> BaseT:
        """Update or create instance.

        Updates instance with the attribute values present on `data`, or creates a new instance if
        one doesn't exist.

        Args:
            data: Instance to update existing, or be created. Identifier used to determine if an
                existing instance exists is the value of an attribute on `data` named as value of
                `self.id_attribute`.

        Returns:
            The updated or created instance.

        Raises:
            RepositoryNotFoundException: If no instance found with same identifier as `data`.
        """
        id_ = self.get_id_attribute_value(data)
        if id_ in self.collection:
            return await self.update(data)
        return await self.add(data, _allow_id=True)
