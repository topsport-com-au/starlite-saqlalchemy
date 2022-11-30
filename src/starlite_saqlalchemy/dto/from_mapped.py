"""Using this implementation instead of the `starlite.SQLAlchemy` plugin DTO as
a POC for using the SQLAlchemy model type annotations to build the pydantic
model.

Also experimenting with marking columns for DTO purposes using the
`SQLAlchemy.Column.info` field, which allows demarcation of fields that
should always be private, or read-only at the model declaration layer.
"""
from __future__ import annotations

from collections import defaultdict
from inspect import getmodule
from types import ModuleType, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    ForwardRef,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, create_model, validator
from pydantic.fields import FieldInfo
from sqlalchemy import Column, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, RelationshipProperty, registry

from starlite_saqlalchemy import settings

from .types import DTOField, Mark, Purpose
from .utils import config

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, Literal, TypeAlias

    from pydantic.typing import AnyClassMethod
    from sqlalchemy.orm import Mapper
    from sqlalchemy.sql.base import ReadOnlyColumnCollection
    from sqlalchemy.util import ReadOnlyProperties

    from .types import DTOConfig

    Registry: TypeAlias = registry


__all__ = ("FromMapped",)

AnyDeclarative = TypeVar("AnyDeclarative", bound=DeclarativeBase)


class _MISSING:
    """A sentinel type to detect if a parameter is supplied or not when.

    constructing pydantic FieldInfo.
    """

    pass


MISSING = _MISSING()


class DTOFactory:
    """Base class for implementing DTO facory.

    Provide methods to inspect SQLAlchemy models and iterating over
    fields to convert.
    """

    def __init__(self, reg: Registry | None = None) -> None:
        self._mapped_classes: dict[str, type[DeclarativeBase]] | None = None
        self._registries: list[Registry] = []
        if reg:
            self._registries.append(reg)
        self._model_modules: set[ModuleType] = set()

    def _inspect_model(
        self, model: type[DeclarativeBase]
    ) -> tuple[ReadOnlyColumnCollection[str, Column], ReadOnlyProperties[RelationshipProperty]]:
        mapper = cast("Mapper", inspect(model))
        columns = mapper.columns
        relationships = mapper.relationships
        return columns, relationships

    def _get_localns(self, model: type[DeclarativeBase]) -> dict[str, Any]:
        localns: dict[str, Any] = self.mapped_classes
        model_module = getmodule(model)
        if model_module is not None:
            self._model_modules.add(model_module)
        for module in self._model_modules:
            localns.update(vars(module))
        return localns

    def _should_exclude_field(
        self,
        purpose: Purpose,
        elem: Column | RelationshipProperty,
        exclude: set[str],
        dto_attrib: DTOField,
    ) -> bool:
        if elem.key in exclude:
            return True
        if dto_attrib.mark is Mark.PRIVATE:
            return True
        if purpose is Purpose.WRITE and dto_attrib.mark is Mark.READ_ONLY:
            return True
        return False

    @property
    def mapped_classes(self) -> dict[str, type[DeclarativeBase]]:
        if not self._registries:
            from starlite_saqlalchemy.db.orm import Base

            self.add_registry(Base.registry)
        if self._mapped_classes is None:
            self._mapped_classes = {}
            for reg in self._registries:
                self._mapped_classes.update(
                    {m.class_.__name__: m.class_ for m in list(reg.mappers)}
                )
        return self._mapped_classes

    def add_registry(self, reg: Registry) -> None:
        self._registries.append(reg)

    def clear_registries(self) -> None:
        self._registries = []
        self._mapped_classes = None

    def get_dto_field(self, elem: Column | RelationshipProperty) -> DTOField:
        return elem.info.get(settings.api.DTO_INFO_KEY, DTOField())

    def is_type_hint_optional(self, type_hint: Any) -> bool:
        origin = get_origin(type_hint)
        if origin is None:
            return False
        if origin is Optional:
            return True
        if origin in (Union, UnionType):
            args = get_args(type_hint)
            return any(arg is type(None) for arg in args)
        return False

    def iter_type_hints(
        self, model: type[DeclarativeBase], purpose: Purpose, exclude: set[str]
    ) -> Generator[tuple[str, Any, Column | RelationshipProperty], None, None]:
        columns, relationships = self._inspect_model(model)

        for key, type_hint in get_type_hints(model, localns=self._get_localns(model)).items():
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

            dto_field = self.get_dto_field(elem)

            if self._should_exclude_field(purpose, elem, exclude, dto_field):
                continue

            yield key, type_hint, elem

    def factory(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class PydanticDTOFactory(DTOFactory):
    """Implements DTO factory using pydantic."""

    def __init__(self, reg: Registry | None = None) -> None:
        super().__init__(reg)
        # List of all existing dtos, both declared and generated
        self.dtos: dict[str, type[FromMapped]] = {}
        # Lis dto's children. Used to update forwardrefs of generated dtos
        self.dto_children: dict[str, list[type[FromMapped]]] = defaultdict(list)
        # Store dto names with fields typed as forwardref.
        self.not_ready: set[str] = set()

    def _construct_field_info(
        self,
        elem: Column | RelationshipProperty,
        purpose: Purpose,
        dto_field: DTOField,
    ) -> FieldInfo:
        if dto_field.pydantic_field is not None:
            return dto_field.pydantic_field

        default_factory = getattr(elem, "default_factory", MISSING)
        default = getattr(elem, "default", MISSING)

        if isinstance(elem, Column):
            if not isinstance(default, _MISSING) and default is not None:
                if default.is_scalar:
                    default = default.arg
                elif default.is_callable:
                    default_factory = lambda: default.arg({})
                else:
                    raise ValueError("Unexpected default type")
        elif isinstance(elem, RelationshipProperty):
            if default is MISSING and elem.uselist:
                default_factory = list
            elif default is MISSING and not elem.uselist:
                default = None

        if purpose is Purpose.READ:
            return FieldInfo(...)
        kwargs = {}
        if default_factory is not MISSING:
            kwargs["default_factory"] = default_factory
        elif default is not MISSING and default_factory is MISSING:
            kwargs["default"] = default
        return FieldInfo(**kwargs)

    def _update_forward_refs(self, dto_name: str) -> None:
        namespace = {**self.dtos}
        if children := self.dto_children.get(dto_name):
            for child in children:
                child.update_forward_refs(**namespace)
            self.dto_children.pop(dto_name)

    def resolve_type(
        self,
        elem: Column | RelationshipProperty,
        type_hint: Any,
        name: str,
        purpose: Purpose,
        parents: list[type[AnyDeclarative]],
        forward_refs: defaultdict[type[DeclarativeBase], list[str]],
        **kwargs: Any,
    ) -> Any:
        if not isinstance(elem, RelationshipProperty):
            return type_hint
        model = elem.mapper.class_
        dto_name = f"{name}_{model.__name__}"
        dto: Any
        if model in parents and len(parents) > 1:
            forward_refs[model].append(dto_name)
            dto = ForwardRef(dto_name)
        else:
            dto = self.factory(
                name=dto_name,
                model=model,
                purpose=purpose,
                parents=parents,
                forward_refs=forward_refs,
                **kwargs,
            )
        if elem.uselist:
            dto = list[dto]
        elif self.is_type_hint_optional(type_hint):
            return dto | None
        return dto

    def factory(
        self,
        name: str,
        model: type[AnyDeclarative],
        purpose: Purpose,
        base: type[BaseModel],
        *_: Any,
        exclude: set[str] | None = None,
        parents: list[type[AnyDeclarative]] | None = None,
        forward_refs: defaultdict[type[DeclarativeBase], list[str]] | None = None,
        **kwargs: Any,
    ) -> type[FromMapped[AnyDeclarative]]:
        if parents is None:
            parents = []
        if forward_refs is None:
            forward_refs = defaultdict(list)

        parents.append(model)
        exclude = set() if exclude is None else exclude
        fields: dict[str, tuple[Any, FieldInfo]] = {}
        validators: dict[str, AnyClassMethod] = {}

        for key, type_hint, elem in self.iter_type_hints(model, purpose, exclude):
            dto_field = self.get_dto_field(elem)

            if dto_field.pydantic_type is not None:
                type_hint = dto_field.pydantic_type

            for i, func in enumerate(dto_field.validators or []):
                validators[f"_validates_{key}_{i}"] = validator(key, allow_reuse=True)(func)

            type_hint = self.resolve_type(
                elem,
                type_hint,
                name,
                purpose,
                parents=parents,
                forward_refs=forward_refs,
                base=base,
                **kwargs,
            )
            fields[key] = (type_hint, self._construct_field_info(elem, purpose, dto_field))

        dto = create_model(  # type: ignore[call-overload]
            name,
            __base__=base,
            __module__=getattr(model, "__module__", __name__),
            __validators__=validators,
            __cls_kwargs__={"model": model},
            **fields,
        )
        dto = cast("type[FromMapped[AnyDeclarative]]", dto)
        self.dtos[name] = dto

        if name != parents[0].__name__:
            self.dto_children[parents[0].__name__].append(dto)
        elif forward_refs:
            self._update_forward_refs(dto.__name__)

        if model_forward_refs := forward_refs.get(model, None):
            for forward_ref in model_forward_refs:
                self.dtos[forward_ref] = dto

        return dto  # type: ignore[no-any-return]


pydantic_dto_factory = PydanticDTOFactory()


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
        cls,
        name: str,
        model: type[AnyDeclarative],
        purpose: Purpose,
        exclude: set[str],
    ) -> type[FromMapped[AnyDeclarative]]:
        return pydantic_dto_factory.factory(
            name=name, model=model, purpose=purpose, exclude=exclude, base=cls
        )
