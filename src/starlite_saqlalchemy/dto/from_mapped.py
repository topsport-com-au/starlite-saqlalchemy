"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

from inspect import getmodule
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Generic,
    TypeVar,
    Union,
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

from .types import DTOField, Mark, Purpose
from .utils import config

if TYPE_CHECKING:
    from typing import Any, Literal

    from pydantic.typing import AnyClassMethod
    from sqlalchemy import Column
    from sqlalchemy.orm import Mapper, RelationshipProperty
    from sqlalchemy.sql.base import ReadOnlyColumnCollection
    from sqlalchemy.util import ReadOnlyProperties

    from .types import DTOConfig

__all__ = ("FromMapped",)


AnyDeclarative = TypeVar("AnyDeclarative", bound=DeclarativeBase)


class FromMapped(BaseModel, Generic[AnyDeclarative]):
    """Produce an SQLAlchemy instance with values from a pydantic model."""

    __sqla_model__: ClassVar[type[DeclarativeBase]]

    class Config:
        """Set orm_mode for `to_mapped()` method."""

        orm_mode = True

    def __class_getitem__(
        cls, item: Annotated[type[AnyDeclarative], DTOConfig | Literal["read", "write"]]
    ) -> type[FromMapped[AnyDeclarative]]:
        """Decorate `cls` with result from `factory()`.

        Args:
            item: Can be either of a SQLAlchemy ORM instance, or a `typing.Annotated` annotation
                where the first argument is a SQLAlchemy ORM instance, and the second is an instance
                of `DTOConfig`.

        Returns:
            A new Pydantic model type, with `cls` as its base class, and additional fields derived
            from the SQLAlchemy model, respecting any declared configuration.
        """
        if get_origin(item) is Annotated:
            model, pos_arg, *_ = get_args(item)
            if isinstance(pos_arg, str):
                dto_config = config(pos_arg)  # type:ignore[arg-type]
            else:
                dto_config = pos_arg
        else:
            raise ValueError("Unexpected type annotation for `FromMapped`.")
        return cls._factory(
            cls.__name__,
            cast("type[AnyDeclarative]", model),
            dto_config.purpose,
            exclude=dto_config.exclude,
        )

    # pylint: disable=arguments-differ
    def __init_subclass__(cls, model: type[AnyDeclarative] | None = None, **kwargs: Any) -> None:
        """Set `__sqla_model__` on type.

        Args:
            model: Model represented by the DTO
            kwargs: Passed to `super().__init_subclass__()`
        """
        super().__init_subclass__(**kwargs)
        if model is not None:
            cls.__sqla_model__ = model

    def to_mapped(self) -> AnyDeclarative:
        """Create an instance of `self.__sqla_model__`

        Fill the bound SQLAlchemy model recursively with values from
        this dataclass.
        """
        as_model = {}
        for pydantic_field in self.__fields__.values():
            value = getattr(self, pydantic_field.name)
            if isinstance(value, (list, tuple)):
                value = [el.to_mapped() if isinstance(el, FromMapped) else el for el in value]
            if isinstance(value, FromMapped):
                value = value.to_mapped()
            as_model[pydantic_field.name] = value
        return cast("AnyDeclarative", self.__sqla_model__(**as_model))

    @classmethod
    def _factory(
        cls, name: str, model: type[DeclarativeBase], purpose: Purpose, exclude: set[str]
    ) -> type[FromMapped[AnyDeclarative]]:
        exclude = set() if exclude is None else exclude

        columns, relationships = _inspect_model(model)
        fields: dict[str, tuple[Any, FieldInfo]] = {}
        validators: dict[str, AnyClassMethod] = {}
        for key, type_hint in get_type_hints(model, localns=_get_localns(model)).items():
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

            dto_field = _get_dto_field(elem)

            if _should_exclude_field(purpose, elem, exclude, dto_field):
                continue

            if dto_field.pydantic_type is not None:
                type_hint = dto_field.pydantic_type

            for i, func in enumerate(dto_field.validators or []):
                validators[f"_validates_{key}_{i}"] = validator(key, allow_reuse=True)(func)

            type_hint = cls._handle_relationships(type_hint, name, purpose)
            fields[key] = (type_hint, _construct_field_info(elem, purpose, dto_field))

        return create_model(  # type:ignore[no-any-return,call-overload]
            name,
            __base__=cls,
            __module__=getattr(model, "__module__", __name__),
            __validators__=validators,
            __cls_kwargs__={"model": model},
            **fields,
        )

    @classmethod
    def _handle_relationships(cls, type_hint: Any, name: str, purpose: Purpose) -> Any:
        args = get_args(type_hint)
        if not args and not issubclass(type_hint, DeclarativeBase):
            return type_hint

        any_decl = any(issubclass(a, DeclarativeBase) for a in args)
        if args and not any_decl:
            return type_hint

        if args:
            origin_type = get_origin(type_hint)
            if origin_type is None:  # pragma: no cover
                raise RuntimeError("Unexpected `None` origin type.")
            origin_type = Union if origin_type is UnionType else origin_type
            inner_types = tuple(cls._handle_relationships(a, name, purpose) for a in args)
            return origin_type[inner_types]  # pyright:ignore

        type_hint = cls._factory(
            f"{name}_{type_hint.__name__}", type_hint, purpose=purpose, exclude=set()
        )
        return type_hint


def _construct_field_info(
    elem: Column | RelationshipProperty, purpose: Purpose, dto_field: DTOField
) -> FieldInfo:
    if dto_field.pydantic_field is not None:
        return dto_field.pydantic_field

    default = getattr(elem, "default", None)
    nullable = getattr(elem, "nullable", False)
    if purpose is Purpose.READ:
        return FieldInfo(...)
    if default is None:
        return FieldInfo(default=None) if nullable else FieldInfo(...)
    if default.is_scalar:
        return FieldInfo(default=default.arg)
    if default.is_callable:
        return FieldInfo(default_factory=lambda: default.arg({}))
    raise ValueError("Unexpected default type")


def _get_dto_field(elem: Column | RelationshipProperty) -> DTOField:
    return elem.info.get(settings.api.DTO_INFO_KEY, DTOField())


def _should_exclude_field(
    purpose: Purpose, elem: Column | RelationshipProperty, exclude: set[str], dto_attrib: DTOField
) -> bool:
    if elem.key in exclude:
        return True
    if dto_attrib.mark is Mark.PRIVATE:
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
