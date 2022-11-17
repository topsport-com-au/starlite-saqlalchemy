"""Repository type definitions."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

FilterTypes = BeforeAfter | CollectionFilter[Any] | LimitOffset
"""Aggregate type alias of the types supported for collection filtering."""


T = TypeVar("T")


class ModelProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for repository models."""

    @classmethod
    def from_dto(cls: type[T], dto_instance: BaseModel) -> T:  # pragma: no cover
        """

        Args:
            dto_instance: A pydantic model.

        Returns:
            Instance of type with values populated from `dto_instance`.
        """
        ...  # pylint: disable=unnecessary-ellipsis


ModelT = TypeVar("ModelT", bound=ModelProtocol)
