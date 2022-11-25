"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

from enum import Enum, auto
from inspect import getmodule, isclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    NamedTuple,
    TypedDict,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, create_model, validator
from pydantic.fields import FieldInfo
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, Mapped

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from pydantic.typing import AnyClassMethod
    from sqlalchemy import Column
    from sqlalchemy.orm import Mapper, RelationshipProperty
    from sqlalchemy.sql.base import ReadOnlyColumnCollection
    from sqlalchemy.util import ReadOnlyProperties


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
    pydantic_type: Any | None = None
    """Override the field type on the pydantic model for this attribute."""
    validators: Iterable[Callable[[Any], Any]] | None = None
    """Single argument callables that are defined on the DTO as validators for the field."""


class _MapperBind(BaseModel, Generic[AnyDeclarative]):
    """Produce an SQLAlchemy instance with values from a pydantic model."""

    __sqla_model__: ClassVar[type[DeclarativeBase]]

    class Config:
        """Set orm_mode for `to_mapped()` method."""

        orm_mode = True

    def __init_subclass__(  # pylint: disable=arguments-differ
        cls, model: type[DeclarativeBase] | None = None, **kwargs: Any
    ) -> None:
        if model is not None:
            cls.__sqla_model__ = model
        super().__init_subclass__(**kwargs)

    def to_mapped(self) -> AnyDeclarative:
        """Create an instance of `self.__sqla_model__`

        Fill the bound SQLAlchemy model recursively with values from
        this dataclass.
        """
        as_model = {}
        for field in self.__fields__.values():
            value = getattr(self, field.name)
            if isinstance(value, (list, tuple)):
                value = [el.to_mapped() if isinstance(el, _MapperBind) else el for el in value]
            if isinstance(value, _MapperBind):
                value = value.to_mapped()
            as_model[field.name] = value
        return cast("AnyDeclarative", self.__sqla_model__(**as_model))


def _construct_field_info(elem: Column | RelationshipProperty, purpose: Purpose) -> FieldInfo:
    default = getattr(elem, "default", None)
    nullable = getattr(elem, "nullable", False)
    if purpose is Purpose.READ:
        return FieldInfo(...)
    if default is None:
        if nullable:
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


def _inspect_model(
    model: type[DeclarativeBase],
) -> tuple[ReadOnlyColumnCollection[str, Column], ReadOnlyProperties[RelationshipProperty]]:
    mapper = cast("Mapper", inspect(model))
    columns = mapper.columns
    relationships = mapper.relationships
    return columns, relationships


def _get_localns(model: type[DeclarativeBase]) -> dict[str, Any]:
    model_module = getmodule(model)
    return vars(model_module) if model_module is not None else {}


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
    name: str,
    model: type[AnyDeclarative],
    purpose: Purpose,
    *,
    exclude: set[str] | None = None,
    base: type[BaseModel] | None = None,
) -> type[_MapperBind[AnyDeclarative]]:
    """Infer a Pydantic model from a SQLAlchemy model.

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
        base: A subclass of `pydantic.BaseModel` to be used as the base class of the DTO.

    Returns:
        A Pydantic model that includes only fields that are appropriate to `purpose` and not in
        `exclude`.
    """
    exclude = set() if exclude is None else exclude

    columns, relationships = _inspect_model(model)
    fields: dict[str, tuple[Any, FieldInfo]] = {}
    validators: dict[str, AnyClassMethod] = {}
    for key, type_hint in get_type_hints(model, localns=_get_localns(model)).items():
        # don't override fields that already exist on `base`.
        if base is not None and key in base.__fields__:
            continue

        if get_origin(type_hint) is Mapped:
            (type_hint,) = get_args(type_hint)

        elem: Column | RelationshipProperty
        if key in columns:
            elem = columns[key]
        elif key in relationships:
            elem = relationships[key]
        else:
            # class var, anything else??
            continue

        attrib = _get_dto_attrib(elem)

        if _should_exclude_field(purpose, elem, exclude, attrib):
            continue

        if attrib.pydantic_type is not None:
            type_hint = attrib.pydantic_type

        for i, func in enumerate(attrib.validators or []):
            validators[f"_validates_{key}_{i}"] = validator(key, allow_reuse=True)(func)

        if isclass(type_hint) and issubclass(type_hint, DeclarativeBase):
            type_hint = factory(f"{name}_{type_hint.__name__}", type_hint, purpose=purpose)

        fields[key] = (type_hint, _construct_field_info(elem, purpose))

    return create_model(  # type:ignore[no-any-return,call-overload]
        name,
        __base__=tuple(filter(None, (base, _MapperBind[AnyDeclarative]))),
        __cls_kwargs__={"model": model},
        __module__=getattr(model, "__module__", __name__),
        __validators__=validators,
        **fields,
    )


def decorator(
    model: type[AnyDeclarative], purpose: Purpose, *, exclude: set[str] | None = None
) -> Callable[[type[BaseModel]], type[_MapperBind[AnyDeclarative]]]:
    """Infer a Pydantic model from SQLAlchemy model."""

    def wrapper(cls: type[BaseModel]) -> type[_MapperBind[AnyDeclarative]]:
        def wrapped() -> type[_MapperBind[AnyDeclarative]]:
            return factory(cls.__name__, model, purpose, exclude=exclude, base=cls)

        return wrapped()

    return wrapper
