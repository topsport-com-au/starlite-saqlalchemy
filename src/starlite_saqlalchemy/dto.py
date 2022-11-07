"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseConfig, BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy.orm import DeclarativeBase, Mapper


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


class Purpose(Enum):
    """For identifying the purpose of a DTO to the factory.

    The factory will exclude fields marked as private or read-only on the domain model depending
    on the purpose of the DTO.

    Example:

    ```python
    ReadDTO = dto.factory("AuthorReadDTO", Author, purpose=dto.Purpose.READ)
    ```
    """

    READ = auto()
    WRITE = auto()


class Attrib(NamedTuple):
    """For configuring DTO behavior on SQLAlchemy model fields."""

    mark: Mark | None = None
    """Mark the field as read only, or skip."""
    pydantic_field: FieldInfo | None = None
    """If provided, used for the pydantic model for this attribute."""


def _construct_field_info(column: Column, purpose: Purpose) -> FieldInfo:
    default = column.default
    if purpose is Purpose.READ or default is None:
        return FieldInfo(...)
    if default.is_scalar:
        return FieldInfo(default=default.arg)  # type:ignore[attr-defined]
    if default.is_callable:
        return FieldInfo(default_factory=lambda: default.arg({}))  # type:ignore[attr-defined]
    raise ValueError("Unexpected default type")


def _get_dto_attrib(column: Column) -> Attrib:
    return column.info.get(settings.api.DTO_INFO_KEY, Attrib())


def _should_exclude_field(
    purpose: Purpose, column: Column, exclude: set[str], dto_attrib: Attrib
) -> bool:
    if column.key in exclude:
        return True
    if dto_attrib.mark is Mark.SKIP:
        return True
    if purpose is Purpose.WRITE and dto_attrib.mark is Mark.READ_ONLY:
        return True
    return False


def factory(
    name: str, model: type[DeclarativeBase], purpose: Purpose, exclude: set[str] | None = None
) -> type[BaseModel]:
    """Create a pydantic model class from a SQLAlchemy declarative ORM class.

    The fields that are included in the model can be controlled on the SQLAlchemy class
    definition by including a "dto" key in the `Column.info` mapping. For example:

    ```python
    class User(DeclarativeBase):
        id: Mapped[UUID] = mapped_column(
            default=uuid4, primary_key=True, info={"dto": Attrib(mark=dto.Mark.READ_ONLY)}
        )
        email: Mapped[str]
        password_hash: Mapped[str] = mapped_column(info={"dto": Attrib(mark=dto.Mark.SKIP)})
    ```

    In the above example, a DTO generated for `Purpose.READ` will include the `id` and `email`
    fields, while a model generated for `Purpose.WRITE` will only include a field for `email`.
    Notice that columns marked as `Mark.SKIP` will not have a field produced in any DTO object.

    Args:
        name: Name given to the DTO class.
        model: The SQLAlchemy model class.
        purpose: Is the DTO for write or read operations?
        exclude: Explicitly exclude attributes from the DTO.

    Returns:
        A Pydantic model that includes only fields that are appropriate to `purpose` and not in
        `exclude`.
    """
    exclude = exclude or set[str]()
    mapper = cast("Mapper", inspect(model))
    columns = mapper.columns
    fields: dict[str, tuple[Any, FieldInfo]] = {}
    for key, type_hint in get_type_hints(model).items():
        if get_origin(type_hint) is not Mapped:
            continue
        column = columns[key]
        attrib = _get_dto_attrib(column)
        if _should_exclude_field(purpose, column, exclude, attrib):
            continue
        (type_,) = get_args(type_hint)
        fields[key] = (type_, _construct_field_info(column, purpose))
    return create_model(  # type:ignore[no-any-return,call-overload]
        name, __config__=type("Config", (BaseConfig,), {"orm_mode": True}), **fields
    )
