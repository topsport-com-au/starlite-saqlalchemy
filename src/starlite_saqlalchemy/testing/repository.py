"""A repository implementation for tests.

Uses a `dict` for storage.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import uuid4

from starlite_saqlalchemy.orm import Base
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

    collection: "abc.MutableMapping[abc.Hashable, BaseT]" = {}

    def __init__(self, id_factory: "abc.Callable[[], Any]" = uuid4, **_: Any) -> None:
        super().__init__()
        self._id_factory = id_factory

    def _find_or_raise_not_found(self, id_: Any) -> BaseT:
        return self.check_not_found(self.collection.get(id_))

    async def add(self, data: BaseT) -> BaseT:
        if self.get_id_attribute_value(data) is not None:
            raise RepositoryConflictException("`add()` received identified item.")
        now = datetime.now()
        data.updated = data.created = now
        id_ = self._id_factory()
        self.set_id_attribute_value(id_, data)
        self.collection[id_] = data
        return data

    async def delete(self, id_: Any) -> BaseT:
        try:
            return self._find_or_raise_not_found(id_)
        finally:
            del self.collection[id_]

    async def get(self, id_: Any) -> BaseT:
        return self._find_or_raise_not_found(id_)

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[BaseT]:
        # TODO: support filters here  # pylint: disable=fixme
        return list(self.collection.values())

    async def update(self, data: BaseT) -> BaseT:
        item = self._find_or_raise_not_found(self.get_id_attribute_value(data))
        # should never be modifiable
        data.updated = datetime.now()
        for key, val in data.__dict__.items():
            if key.startswith("_"):
                continue
            setattr(item, key, val)
        return item

    async def upsert(self, data: BaseT) -> BaseT:
        if await self.get_id_attribute_value(data) is None:
            return await self.add(data)
        return await self.update(data)
