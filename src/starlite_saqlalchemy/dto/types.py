"""DTO domain types."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Any

    from pydantic.fields import FieldInfo

__all__ = (
    "AnyDeclarative",
    "DTOConfig",
    "Field",
    "Mark",
    "Purpose",
)

AnyDeclarative = TypeVar("AnyDeclarative", bound=DeclarativeBase)


class Mark(str, Enum):
    """For marking column definitions on the domain models.

    Example:
    ```python
    class Model(Base):
        ...
        updated_at: Mapped[datetime] = mapped_column(info={"dto": Mark.READ_ONLY})
    ```
    """

    READ_ONLY = "read-only"
    SKIP = "skip"


class Purpose(str, Enum):
    """For identifying the purpose of a DTO to the factory.

    The factory will exclude fields marked as private or read-only on the domain model depending
    on the purpose of the DTO.

    Example:
    ```python
    ReadDTO = dto.factory("AuthorReadDTO", Author, purpose=dto.Purpose.READ)
    ```
    """

    READ = "read"
    WRITE = "write"


@dataclass
class Field:
    """For configuring DTO behavior on SQLAlchemy model fields."""

    mark: Mark | None = None
    """Mark the field as read only, or skip."""
    pydantic_type: Any | None = None
    """Override the field type on the pydantic model for this attribute."""
    pydantic_field: FieldInfo | None = None
    """If provided, used for the pydantic model for this attribute."""
    validators: Iterable[Callable[[Any], Any]] | None = None
    """Single argument callables that are defined on the DTO as validators for the field."""


@dataclass
class DTOConfig:
    """Control the generated DTO."""

    purpose: Purpose = Purpose.WRITE
    exclude: set[str] = field(default_factory=set)
