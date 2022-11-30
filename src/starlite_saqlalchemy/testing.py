"""A repository implementation for tests.

Uses a `dict` for storage.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import uuid4

from starlite_saqlalchemy.db import orm
from starlite_saqlalchemy.repository.abc import AbstractRepository
from starlite_saqlalchemy.repository.exceptions import RepositoryConflictException

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Iterable, MutableMapping

    from starlite_saqlalchemy.repository.types import FilterTypes

ModelT = TypeVar("ModelT", bound=orm.Base)
MockRepoT = TypeVar("MockRepoT", bound="GenericMockRepository")


class GenericMockRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """A repository implementation for tests.

    Uses a `dict` for storage.
    """

    collection: MutableMapping[Hashable, ModelT] = {}
    model_type: type[ModelT]

    def __init__(self, id_factory: Callable[[], Any] = uuid4, **_: Any) -> None:
        super().__init__()
        self._id_factory = id_factory

    @classmethod
    def __class_getitem__(cls: type[MockRepoT], item: type[ModelT]) -> type[MockRepoT]:
        """Add collection to `_collections` for the type.

        Args:
            item: The type that the class has been parametrized with.
        """
        return type(  # pyright:ignore
            f"{cls.__name__}[{item.__name__}]", (cls,), {"collection": {}, "model_type": item}
        )

    def _find_or_raise_not_found(self, id_: Any) -> ModelT:
        return self.check_not_found(self.collection.get(id_))

    async def add(self, data: ModelT, allow_id: bool = False) -> ModelT:
        """Add `data` to the collection.

        Args:
            data: Instance to be added to the collection.
            allow_id: disable the identified object check.

        Returns:
            The added instance.
        """
        if allow_id is False and self.get_id_attribute_value(data) is not None:
            raise RepositoryConflictException("`add()` received identified item.")
        now = datetime.now()
        data.updated = data.created = now
        if allow_id is False:
            id_ = self._id_factory()
            self.set_id_attribute_value(id_, data)
        self.collection[data.id] = data
        return data

    async def delete(self, id_: Any) -> ModelT:
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

    async def get(self, id_: Any) -> ModelT:
        """Get instance identified by `id_`.

        Args:
            id_: Identifier of the instance to be retrieved.

        Returns:
            The retrieved instance.

        Raises:
            RepositoryNotFoundException: If no instance found identified by `id_`.
        """
        return self._find_or_raise_not_found(id_)

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[ModelT]:
        """Get a list of instances, optionally filtered.

        Args:
            *filters: Types for specific filtering operations.
            **kwargs: Instance attribute value filters.

        Returns:
            The list of instances, after filtering applied.
        """
        return list(self.collection.values())

    async def update(self, data: ModelT) -> ModelT:
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

    async def upsert(self, data: ModelT) -> ModelT:
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
        return await self.add(data, allow_id=True)

    @classmethod
    def seed_collection(cls, instances: Iterable[ModelT]) -> None:
        """Seed the collection for repository type.

        Args:
            instances: the instances to be added to the collection.
        """
        for instance in instances:
            cls.collection[cls.get_id_attribute_value(instance)] = instance

    @classmethod
    def clear_collection(cls) -> None:
        """Empty the collection for repository type."""
        cls.collection = {}
