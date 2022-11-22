"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from enum import Enum, auto
from inspect import isclass
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    TypedDict,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseConfig as BaseConfig_
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, Mapped

from starlite_saqlalchemy import settings

from .pydantic import _VALIDATORS

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy.orm import Mapper, RelationshipProperty



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


class DTOInfo(TypedDict):
    """Represent dto infos suitable for info mapped_column infos param."""
    dto: Attrib


class Attrib(NamedTuple):
    """For configuring DTO behavior on SQLAlchemy model fields."""

    mark: Mark | None = None
    """Mark the field as read only, or skip."""
    pydantic_field: FieldInfo | None = None
    """If provided, used for the pydantic model for this attribute."""


class BaseConfig(BaseConfig_):
    """Base config for generated pydantic models"""
    orm_mode = True


class MapperBind(BaseModel):
    """Produce an SQLAlchemy instance with values from a pydantic model."""
    __sqla_model__: type[DeclarativeBase]

    class Config(BaseConfig):
        """Config for MapperBind pydantic models."""

    def __init_subclass__(cls, model: type[DeclarativeBase]) -> None:
        cls.__sqla_model__ = model
        return super().__init_subclass__()

    def mapper(self) -> DeclarativeBase:
        """Fill the binded SQLAlchemy model recursively with values from this
        dataclass."""
        as_model = {}
        for field in self.__fields__.values():
            value = getattr(self, field.name)
            if isinstance(value, (list, tuple)):
                value = [el.mapper() if isinstance(el, MapperBind) else el for el in value]
            if isinstance(value, MapperBind):
                value = value.mapper()
            as_model[field.name] = value
        return self.__sqla_model__(**as_model)


def _construct_field_info(elem: Column | RelationshipProperty, purpose: Purpose) -> FieldInfo:
    default = getattr(elem, "default", None)
    nullable = getattr(elem, "nullable", False)
    if purpose is Purpose.READ:
        return FieldInfo(...)
    if default is None:
        if not nullable:
            return FieldInfo(default=None)
        return FieldInfo(...)
    if default.is_scalar:
        return FieldInfo(default=default.arg)
    if default.is_callable:
        return FieldInfo(default_factory=lambda: default.arg({}))
    raise ValueError("Unexpected default type")


def _get_dto_attrib(elem: Column | RelationshipProperty) -> Attrib:
    return elem.info.get(settings.api.DTO_INFO_KEY, Attrib())


def _should_exclude_field(
    purpose: Purpose, elem: Column | RelationshipProperty, exclude: set[str], dto_attrib: Attrib
) -> bool:
    if elem.key in exclude:
        return True
    if dto_attrib.mark is Mark.SKIP:
        return True
    if purpose is Purpose.WRITE and dto_attrib.mark is Mark.READ_ONLY:
        return True
    return False


def mark(mark_type: Mark) -> DTOInfo:
    """Shortcut for ```python.

    {"dto": Attrib(mark=mark_type)}
    ```

    Example:

    ```python
    class User(DeclarativeBase):
        id: Mapped[UUID] = mapped_column(
            default=uuid4, primary_key=True, info=dto.mark(dto.Mark.READ_ONLY)
        )
        email: Mapped[str]
        password_hash: Mapped[str] = mapped_column(info=dto.mark(dto.Mark.SKIP))
    ```

    Args:
        mark_type: dto Mark

    Returns:
        A `DTOInfo` suitable to pass to `info` param of `mapped_column`
    """
    return {"dto": Attrib(mark=mark_type)}


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
    relationships = mapper.relationships
    fields: dict[str, tuple[Any, FieldInfo]] = {}
    for key, type_hint in get_type_hints(model).items():
        if get_origin(type_hint) is not Mapped:
            continue
        elem: Column | RelationshipProperty
        try:
            elem = columns[key]
        except KeyError:
            elem = relationships[key]
        attrib = _get_dto_attrib(elem)
        if _should_exclude_field(purpose, elem, exclude, attrib):
            continue
        (type_,) = get_args(type_hint)
        if isclass(type_) and issubclass(type_, DeclarativeBase):
            type_ = factory(f"{name}_{type_.__name__}", type_, purpose=purpose)
        fields[key] = (type_, _construct_field_info(elem, purpose))
    return create_model(  # type:ignore[no-any-return,call-overload]
        name,
        __config__=type("Config", (BaseConfig,), {}),
        __module__=getattr(model, "__module__", "starlite_saqlalchemy.dto"),
        **fields,
    )


def dto(
    model: type[DeclarativeBase],
    purpose: Purpose,
    exclude: set[str] | None = None,
    mapper_bind: bool = True,
) -> Callable[[type], type[BaseModel]]:
    """Create a pydantic model class from a SQLAlchemy declarative ORM class
    with validation support.

    This decorator is not recursive so relationships will be ignored (but can be
    overridden on the decorated class).

    Pydantic validation is supported using `validator` decorator from `starlite_sqlalchemy.pydantic`

    As for the `factory` function, included fields can be controlled on the SQLAlchemy class
    definition by including a "dto" key in the `Column.info` mapping.

    Example:
    ```python
    class User(DeclarativeBase):
        id: Mapped[UUID] = mapped_column(
            default=uuid4, primary_key=True, info={"dto": Attrib(mark=dto.Mark.READ_ONLY)}
        )
        email: Mapped[str]
        password_hash: Mapped[str] = mapped_column(info={"dto": Attrib(mark=dto.Mark.SKIP)})


    @dto.dto(User, Purpose.WRITE)
    class UserCreate:
        @dto.validator("email")
        def val_email(cls, v):
            if "@" not in v:
                raise ValueError("Invalid email")
    ```

    When setting `mapper_bind` (default to `True`), the resulting pydantic model will have a `mapper` method
    that can be used to create an instance of the original SQLAlchemy model with values from the pydantic one:

    ```python
    @dto.dto(User, Purpose.WRITE)
    class UserCreate:
        pass


    user = UserCreate(email="john@email.me")
    user_model = user.mapper()  # user_model is a User instance
    ```

    Args:
        model: The SQLAlchemy model class.
        purpose: Is the DTO for write or read operations?
        exclude: Explicitly exclude attributes from the DTO.
        mapper_bind: Add a `mapper()` method that return an instance of the original SQLAlchemy model with values from the pydantic model.
    Returns:
        A Pydantic model that includes only fields that are appropriate to `purpose` and not in
        `exclude`, except relationship fields.
    """

    def wrapper(cls: type) -> type[BaseModel]:
        def wrapped() -> type[BaseModel]:
            exclude_ = exclude or set[str]()
            mapper = cast("Mapper", inspect(model))
            columns = mapper.columns
            relationships = mapper.relationships
            fields: dict[str, tuple[Any, FieldInfo]] = {}
            name = cls.__name__
            namespace = {
                **sys.modules[model.__module__].__dict__,
                **sys.modules[cls.__module__].__dict__,
            }
            type_hints = {
                **get_type_hints(model, localns=namespace),
                **cls.__annotations__,
            }
            for key, type_hint in type_hints.items():
                elem: Column | RelationshipProperty
                try:
                    elem = columns[key]
                except KeyError:
                    elem = relationships[key]
                attrib = _get_dto_attrib(elem)
                if _should_exclude_field(purpose, elem, exclude_, attrib):
                    continue
                type_ = type_hint
                if key in relationships and key not in cls.__annotations__:
                    continue
                fields[key] = (type_, _construct_field_info(elem, purpose))
            return create_model(  # type:ignore[no-any-return,call-overload]
                name,
                __module__=getattr(model, "__module__", __name__),
                __base__=MapperBind if mapper_bind else None,
                __cls_kwargs__={"model": model},
                __validators__=_VALIDATORS[f"{cls.__module__}.{cls.__name__}"],
                **fields,
            )

        return wrapped()

    return wrapper
