"""Data persistence interface."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from starlite_saqlalchemy.exceptions import NotFoundError

if TYPE_CHECKING:
    from .types import FilterTypes

__all__ = ["AbstractRepository"]

T = TypeVar("T")
RepoT = TypeVar("RepoT", bound="AbstractRepository")


class AbstractRepository(Generic[T], metaclass=ABCMeta):
    """Interface for persistent data interaction."""

    model_type: type[T]
    """Type of object represented by the repository."""
    id_attribute = "id"
    """Name of the primary identifying attribute on `model_type`."""

    def __init__(self, **kwargs: Any) -> None:
        """Repository constructors accept arbitrary kwargs."""
        super().__init__(**kwargs)

    @abstractmethod
    async def add(self, data: T) -> T:
        """Add `data` to the collection.

        Args:
            data: Instance to be added to the collection.

        Returns:
            The added instance.
        """

    @abstractmethod
    async def delete(self, id_: Any) -> T:
        """Delete instance identified by `id_`.

        Args:
            id_: Identifier of instance to be deleted.

        Returns:
            The deleted instance.

        Raises:
            RepositoryNotFoundException: If no instance found identified by `id_`.
        """

    @abstractmethod
    async def get(self, id_: Any) -> T:
        """Get instance identified by `id_`.

        Args:
            id_: Identifier of the instance to be retrieved.

        Returns:
            The retrieved instance.

        Raises:
            RepositoryNotFoundException: If no instance found identified by `id_`.
        """

    @abstractmethod
    async def list(self, *filters: FilterTypes, **kwargs: Any) -> list[T]:
        """Get a list of instances, optionally filtered.

        Args:
            *filters: Types for specific filtering operations.
            **kwargs: Instance attribute value filters.

        Returns:
            The list of instances, after filtering applied.
        """

    @abstractmethod
    async def update(self, data: T) -> T:
        """Update instance with the attribute values present on `data`.

        Args:
            data: An instance that should have a value for `self.id_attribute` that exists in the
                collection.

        Returns:
            The updated instance.

        Raises:
            RepositoryNotFoundException: If no instance found with same identifier as `data`.
        """

    @abstractmethod
    async def upsert(self, data: T) -> T:
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

    @abstractmethod
    def filter_collection_by_kwargs(self, **kwargs: Any) -> None:
        """Filter the collection by kwargs.

        Has `AND` semantics where multiple kwargs name/value pairs are provided.

        Args:
            **kwargs: key/value pairs such that objects remaining in the collection after filtering
                have the property that their attribute named `key` has value equal to `value`.

        Raises:
            RepositoryException: if a named attribute doesn't exist on `self.model_type`.
        """

    @staticmethod
    def check_not_found(item_or_none: T | None) -> T:
        """Raise `RepositoryNotFoundException` if `item_or_none` is `None`.

        Args:
            item_or_none: Item to be tested for existence.

        Returns:
            The item, if it exists.
        """
        if item_or_none is None:
            raise NotFoundError("No item found when one was expected")
        return item_or_none

    @classmethod
    def get_id_attribute_value(cls, item: T) -> Any:
        """Get value of attribute named as `self.id_attribute` on `item`.

        Args:
            item: Anything that should have an attribute named as `self.id_attribute` value.

        Returns:
            The value of attribute on `item` named as `self.id_attribute`.
        """
        return getattr(item, cls.id_attribute)

    @classmethod
    def set_id_attribute_value(cls, id_: Any, item: T) -> Any:
        """Return the `item` after the ID is set to the appropriate attribute.

        Args:
            id_: Value of ID to be set on instance
            item: Anything that should have an attribute named as `self.id_attribute` value.

        Returns:
            Item with `id_` set to `cls.id_attribute`
        """
        setattr(item, cls.id_attribute, id_)
        return item
