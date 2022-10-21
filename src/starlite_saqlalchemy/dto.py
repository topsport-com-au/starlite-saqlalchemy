"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, get_type_hints

from pydantic import BaseConfig, BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy.orm import DeclarativeBase, Mapper

DTO_INFO_KEY = "dto"


class Mode(Enum):
    """For marking column definitions on the domain models.

    Example:

        ```python
        class Model(Base):
            ...
            updated_at: Mapped[datetime] = mapped_column(info={"dto": Mode.READ_ONLY})
        ```
    """

    READ_ONLY = auto()
    PRIVATE = auto()


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


def _construct_field_info(column: "Column", purpose: Purpose) -> FieldInfo:
    default = column.default
    if purpose is Purpose.READ or default is None:
        return FieldInfo(...)
    if default.is_scalar:
        return FieldInfo(default=default.arg)  # type:ignore[attr-defined]
    if default.is_callable:
        return FieldInfo(default_factory=lambda: default.arg({}))  # type:ignore[attr-defined]
    raise ValueError("Unexpected default type")


def _should_exclude_field(purpose: Purpose, column: "Column", exclude: set[str]) -> bool:
    if column.key in exclude:
        return True
    mode = column.info.get(DTO_INFO_KEY)
    if mode is Mode.PRIVATE:
        return True
    if purpose is Purpose.WRITE and mode is Mode.READ_ONLY:
        return True
    return False


def factory(
    name: str, model: type["DeclarativeBase"], purpose: Purpose, exclude: set[str] | None = None
) -> type[BaseModel]:
    """Create a pydantic model class from a SQLAlchemy declarative ORM class.

    The fields that are included in the model can be controlled on the SQLAlchemy class
    definition by including a "dto" key in the `Column.info` mapping. For example:

        ```python
        class User(DeclarativeBase):
            id: Mapped[UUID] = mapped_column(
                default=uuid4, primary_key=True, info={"dto": dto.Mode.READ_ONLY}
            )
            email: Mapped[str]
            password_hash: Mapped[str] = mapped_column(info={"dto": dto.Mode.PRIVATE})
        ```

    In the above example, a DTO generated for `Purpose.READ` will include the `id` and `email`
    fields, while a model generated for `Purpose.WRITE` will only include a field for `email`.
    Notice that columns marked as `Mode.PRIVATE` will not have a field produced in any DTO object.

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
    dto_fields: dict[str, tuple[Any, FieldInfo]] = {}
    for key, type_hint in get_type_hints(model).items():
        if get_origin(type_hint) is not Mapped:
            continue
        column = columns[key]
        if _should_exclude_field(purpose, column, exclude):
            continue
        (type_,) = get_args(type_hint)
        dto_fields[key] = (type_, _construct_field_info(column, purpose))
    return create_model(  # type:ignore[no-any-return,call-overload]
        name, __config__=type("Config", (BaseConfig,), {"orm_mode": True}), **dto_fields
    )
