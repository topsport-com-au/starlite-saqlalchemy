"""A repository implementation for tests.

Uses a `dict` for storage.
"""
from __future__ import annotations

import random
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import uuid4

from starlite.status_codes import HTTP_200_OK, HTTP_201_CREATED

from starlite_saqlalchemy.db import orm
from starlite_saqlalchemy.exceptions import ConflictError, StarliteSaqlalchemyError
from starlite_saqlalchemy.repository.abc import AbstractRepository

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        Generator,
        Hashable,
        Iterable,
        MutableMapping,
        Sequence,
    )
    from typing import Any

    from pydantic import BaseSettings
    from pytest import MonkeyPatch
    from starlite.testing import TestClient

    from starlite_saqlalchemy.repository.types import FilterTypes
    from starlite_saqlalchemy.service import Service

ModelT = TypeVar("ModelT", bound=orm.Base)
MockRepoT = TypeVar("MockRepoT", bound="GenericMockRepository")


@contextmanager
def modify_settings(*update: tuple[BaseSettings, dict[str, Any]]) -> Generator[None, None, None]:
    """Context manager that modify the desired settings and restore them on
    exit.

    >>> assert settings.app.ENVIRONMENT = "local"
    >>> with modify_settings((settings.app, {"ENVIRONMENT": "prod"})):
    >>>     assert settings.app.ENVIRONMENT == "prod"
    >>> assert settings.app.ENVIRONMENT == "local"
    """
    old_settings: list[tuple[BaseSettings, dict[str, Any]]] = []
    try:
        for model, new_values in update:
            old_values = {}
            for field, value in model.dict().items():
                if field in new_values:
                    old_values[field] = value
                    setattr(model, field, new_values[field])
            old_settings.append((model, old_values))
        yield
    finally:
        for model, old_values in old_settings:
            for field, old_val in old_values.items():
                setattr(model, field, old_val)


class GenericMockRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """A repository implementation for tests.

    Uses a `dict` for storage.
    """

    collection: MutableMapping[Hashable, ModelT]
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
            raise ConflictError("`add()` received identified item.")
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

    def filter_collection_by_kwargs(self, **kwargs: Any) -> None:
        """Filter the collection by kwargs.

        Args:
            **kwargs: key/value pairs such that objects remaining in the collection after filtering
                have the property that their attribute named `key` has value equal to `value`.
        """
        new_collection: dict[Hashable, ModelT] = {}
        for item in self.collection.values():
            try:
                if all(getattr(item, name) == value for name, value in kwargs.items()):
                    new_collection[item.id] = item
            except AttributeError as orig:
                raise StarliteSaqlalchemyError from orig
        self.collection = new_collection

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


class ControllerTest:
    """Standard controller testing utility."""

    def __init__(
        self,
        client: TestClient,
        base_path: str,
        collection: Sequence[orm.Base],
        raw_collection: Sequence[dict[str, Any]],
        service_type: type[Service],
        monkeypatch: MonkeyPatch,
        collection_filters: dict[str, Any] | None = None,
    ) -> None:
        """Perform standard tests of controllers.

        Args:
            client: Test client instance.
            base_path: Path for POST and collection GET requests.
            collection: Collection of domain objects.
            raw_collection: Collection of raw representations of domain objects.
            service_type: The domain Service object type.
            monkeypatch: Pytest's monkeypatch.
            collection_filters: Collection filters for GET collection request.
        """
        self.client = client
        self.base_path = base_path
        self.collection = collection
        self.raw_collection = raw_collection
        self.service_type = service_type
        self.monkeypatch = monkeypatch
        self.collection_filters = collection_filters

    def _get_random_member(self) -> Any:
        return random.choice(self.collection)

    def _get_raw_for_member(self, member: Any) -> dict[str, Any]:
        return [item for item in self.raw_collection if item["id"] == str(member.id)][0]

    def test_get_collection(self, with_filters: bool = False) -> None:
        """Test collection endpoint get request."""

        async def _list(*_: Any, **__: Any) -> list[Any]:
            return list(self.collection)

        self.monkeypatch.setattr(self.service_type, "list", _list)

        resp = self.client.get(
            self.base_path, params=self.collection_filters if with_filters else None
        )

        assert resp.status_code == HTTP_200_OK
        assert resp.json() == self.raw_collection

    def test_member_request(self, method: str, service_method: str, exp_status: int) -> None:
        """Test member endpoint request."""
        member = self._get_random_member()
        raw = self._get_raw_for_member(member)

        async def _method(*_: Any, **__: Any) -> Any:
            return member

        self.monkeypatch.setattr(self.service_type, service_method, _method)

        if method.lower() == "post":
            url = self.base_path
        else:
            url = f"{self.base_path}/{member.id}"

        request_kw: dict[str, Any] = {}
        if method.lower() in ("put", "post"):
            request_kw["json"] = raw

        resp = self.client.request(method, url, **request_kw)

        assert resp.status_code == exp_status
        assert resp.json() == raw

    def run(self) -> None:
        """Run the tests."""
        # test the collection route with and without filters for branch coverage.
        self.test_get_collection()
        if self.collection_filters:
            self.test_get_collection(with_filters=True)
        for method, service_method, status in [
            ("GET", "get", HTTP_200_OK),
            ("PUT", "update", HTTP_200_OK),
            ("POST", "create", HTTP_201_CREATED),
            ("DELETE", "delete", HTTP_200_OK),
        ]:
            self.test_member_request(method, service_method, status)
