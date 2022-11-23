"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

from enum import Enum, auto
from inspect import get_annotations, getmodule, isclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
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
    from collections.abc import Callable

    from pydantic.typing import AnyClassMethod
    from sqlalchemy import Column
    from sqlalchemy.orm import Mapper, RelationshipProperty
    from sqlalchemy.sql.base import ReadOnlyColumnCollection
    from sqlalchemy.util import ReadOnlyProperties


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
    """Base config for generated pydantic models."""

    orm_mode = True


class MapperBind(BaseModel):
    """Produce an SQLAlchemy instance with values from a pydantic model."""

    __sqla_model__: ClassVar[type[DeclarativeBase]]

    class Config(BaseConfig):
        """Config for MapperBind pydantic models."""

    @classmethod
    def __init_subclass__(cls, model: type[DeclarativeBase], *args: Any, **kwargs: Any) -> None:
        """Set `__sqla_model__` class var.

        Args:
            model: SQLAlchemy model represented by the DTO.
        """
        cls.__sqla_model__ = model
        return super().__init_subclass__(*args, **kwargs)

    def to_mapped(self) -> DeclarativeBase:
        """Create an instance of `self.__sqla_model__`

        Fill the bound SQLAlchemy model recursively with values from
        this dataclass.
        """
        as_model = {}
        for field in self.__fields__.values():
            value = getattr(self, field.name)
            if isinstance(value, (list, tuple)):
                value = [el.to_mapped() if isinstance(el, MapperBind) else el for el in value]
            if isinstance(value, MapperBind):
                value = value.to_mapped()
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


def _inspect_model(
    model: type[DeclarativeBase],
) -> tuple[ReadOnlyColumnCollection[str, Column], ReadOnlyProperties[RelationshipProperty]]:
    mapper = cast("Mapper", inspect(model))
    columns = mapper.columns
    relationships = mapper.relationships
    return columns, relationships


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


def factory(  # pylint: disable=too-many-locals
    name: str,
    model: type[DeclarativeBase],
    purpose: Purpose,
    exclude: set[str] | None = None,
    namespace: dict[str, Any] | None = None,
    annotations: dict[str, Any] | None = None,
    validators: dict[str, AnyClassMethod] | None = None,
    base: type[BaseModel] | None = MapperBind,
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
        namespace: Additional namespace used to resolve forward references. The default namespace
            used is that of the module of `model`.
        annotations: Annotations that override and supplement the annotations derived from `model`.
        validators: Mapping of attribute name, to pydantic validators.
        base: A subclass of `pydantic.BaseModel` to be used as the base class of the DTO.

    Returns:
        A Pydantic model that includes only fields that are appropriate to `purpose` and not in
        `exclude`.
    """
    exclude_ = exclude or set[str]()
    annotations_ = annotations or {}
    namespace_ = namespace or {}
    validators_ = validators or {}
    del exclude, annotations, namespace, validators
    columns, relationships = _inspect_model(model)
    model_module = getmodule(model)
    localns = vars(model_module) if model_module is not None else {}
    localns.update(namespace_)
    type_hints = get_type_hints(model, localns=localns)
    type_hints.update(annotations_)
    fields: dict[str, tuple[Any, FieldInfo]] = {}
    for key, type_hint in type_hints.items():
        if get_origin(type_hint) is Mapped:
            (type_,) = get_args(type_hint)
        elif type_hint in annotations_:
            type_ = type_hint
        else:
            continue

        elem: Column | RelationshipProperty
        try:
            elem = columns[key]
        except KeyError:
            elem = relationships[key]
        attrib = _get_dto_attrib(elem)
        if _should_exclude_field(purpose, elem, exclude_, attrib):
            continue

        if isclass(type_) and issubclass(type_, DeclarativeBase):
            type_ = factory(f"{name}_{type_.__name__}", type_, purpose=purpose)

        fields[key] = (type_, _construct_field_info(elem, purpose))

    return create_model(  # type:ignore[no-any-return,call-overload]
        name,
        __module__=getattr(model, "__module__", __name__),
        __base__=base,
        __cls_kwargs__={"model": model},
        __validators__=validators_ or {},
        **fields,
    )


def decorator(
    model: type[DeclarativeBase],
    purpose: Purpose,
    exclude: set[str] | None = None,
    base: type[BaseModel] | None = MapperBind,
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
        base: Used as base class for DTO if provided.

    Returns:
        A Pydantic model that includes only fields that are appropriate to `purpose` and not in
        `exclude`, except relationship fields.
    """

    def wrapper(cls: type) -> type[BaseModel]:
        def wrapped() -> type[BaseModel]:
            name = cls.__name__
            cls_module = getmodule(cls)
            namespace = vars(cls_module) if cls_module is not None else {}
            return factory(
                name=name,
                model=model,
                purpose=purpose,
                exclude=exclude,
                namespace=namespace,
                annotations=get_annotations(cls),
                validators=_VALIDATORS[f"{cls.__module__}.{cls.__name__}"],
                base=base,
            )

        return wrapped()

    return wrapper
