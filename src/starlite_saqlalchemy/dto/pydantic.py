"""Pydantic DTO implementation."""

from __future__ import annotations

import builtins
from inspect import signature
from typing import TYPE_CHECKING, Annotated, Literal, cast, get_args, get_origin

from pydantic import BaseModel, create_model, validator
from pydantic.fields import FieldInfo
from sqlalchemy import Column
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty, registry

from .from_mapped import DTO, AnyDeclarative, DTOFactory, FromMappedBase
from .types import DTOField, Purpose
from .utils import config

if TYPE_CHECKING:
    from collections import defaultdict
    from typing import Any, TypeAlias

    from pydantic.typing import AnyClassMethod

    from .types import DTOConfig

    Registry: TypeAlias = registry

__all__ = ["FromMapped"]


class _MISSING:
    """A sentinel type to detect if a parameter is supplied or not when.

    constructing pydantic FieldInfo.
    """


MISSING = _MISSING()


class FromMapped(BaseModel, FromMappedBase[BaseModel, AnyDeclarative]):
    """Produce an SQLAlchemy instance with values from a pydantic model."""

    class Config:
        """Set orm_mode for `to_mapped()` method."""

        orm_mode = True

    def __class_getitem__(
        cls, item: Annotated[type[AnyDeclarative], DTOConfig | Literal["read", "write"]]
    ) -> type[FromMappedBase[BaseModel, AnyDeclarative]]:
        """Build a DTO using class parameter.

        Args:
            item: Annotated type containing
                the SQLAlchemy model to build the DTO from and the DTO config

        Raises:
            ValueError: item is not an Annotated type

        Returns:
            A DTO generated after the given SQLAlchemy model
        """
        if get_origin(item) is Annotated:
            model, pos_arg, *_ = get_args(item)
            dto_config = (
                config(pos_arg)  # type:ignore[arg-type]
                if isinstance(pos_arg, str)
                else pos_arg
            )
        else:
            raise ValueError("Unexpected type annotation for `FromMapped`.")
        return cls._factory(
            f"{cls.__name__}_{model.__name__}",
            cast("type[AnyDeclarative]", model),
            dto_config.purpose,
            exclude=dto_config.exclude,
        )

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
    ) -> type[FromMappedBase[BaseModel, AnyDeclarative]]:
        return pydantic_dto_factory.factory(
            name=name, model=model, purpose=purpose, exclude=exclude, base=cls
        )


class PydanticDTOFactory(DTOFactory[BaseModel]):
    """Implements DTO factory using pydantic."""

    def __init__(self, reg: Registry | None = None) -> None:
        super().__init__(reg)
        # Store dto names with fields typed as forwardref.
        self.not_ready: set[str] = set()

    def _construct_field_info(  # pylint: disable=too-many-branches
        self,
        elem: Column | RelationshipProperty,
        purpose: Purpose,
        dto_field: DTOField,
    ) -> FieldInfo:
        """Build a `FieldInfo instance reflecting the given
        column/relationship.`

        Args:
            elem: Column or relationship from which to generate the FieldInfo
            purpose: DTO purpose
            dto_field: DTOField

        Raises:
            ValueError: Raised when a column default value can't be used on a FieldInfo

        Returns:
            A `FieldInfo` instance
        """
        if dto_field.pydantic_field is not None:
            return dto_field.pydantic_field

        default_factory = getattr(elem, "default_factory", MISSING)
        default = getattr(elem, "default", MISSING)

        if isinstance(elem, Column):
            if not isinstance(default, _MISSING) and default is not None:
                if default.is_scalar:
                    default = default.arg
                elif default.is_callable:
                    if isinstance(default.arg, staticmethod):
                        default_callable = default.arg.__func__
                    else:
                        default_callable = default.arg
                    if (
                        # Eager test because inspect.signature() does not
                        # recognize builtins
                        hasattr(builtins, default_callable.__name__)
                        # If present, context contains information about the current
                        # statement and can be used to access values from other columns.
                        # As we can't reproduce such context in Pydantic, we don't want
                        # include a default_factory in that case.
                        or "context" not in signature(default_callable).parameters
                    ):
                        default_factory = lambda: default.arg({})  # pylint: disable=C3001
                    else:
                        default = MISSING
                else:
                    raise ValueError("Unexpected default type")
            elif default is None and not elem.nullable:
                default = MISSING
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
        """Recursively update forward refs of the dto with the given class
        name.

        Any factory-generated DTO and referenced by
        the given parent will be updated too.

        Args:
            dto_name: Class name of the DTO to update.
        """
        namespace = {**self.dtos}
        if children := self.dto_children.get(dto_name):
            for child in children:
                child.update_forward_refs(**namespace)  # type: ignore
            self.dto_children.pop(dto_name)

    def _factory(  # pylint: disable=too-many-locals
        self,
        name: str,
        root_dto_name: str | None,
        model: type[AnyDeclarative],
        purpose: Purpose,
        base: type[BaseModel] | None,
        exclude: set[str],
        parents: defaultdict[Column | RelationshipProperty, set[type[AnyDeclarative]]],
        forward_refs: defaultdict[type[DeclarativeBase], set[str]],
        level: int = 0,
        root: Column | RelationshipProperty | None = None,
        **kwargs: Any,
    ) -> type[FromMappedBase[DTO, AnyDeclarative]]:
        fields: dict[str, tuple[Any, FieldInfo]] = {}
        validators: dict[str, AnyClassMethod] = {}

        for context in self.iter_type_hints(model, purpose, exclude, level, root):
            key, type_hint, elem, root, level = context
            dto_field = self.get_dto_field(elem)

            if dto_field.pydantic_type is not None:
                type_hint = dto_field.pydantic_type

            for i, func in enumerate(dto_field.validators or []):
                validators[f"_validates_{key}_{i}"] = validator(key, allow_reuse=True)(func)

            type_hint = self._resolve_type(
                elem,
                type_hint,
                name,
                purpose,
                parents=parents,
                root=root,
                level=level,
                forward_refs=forward_refs,
                base=base,
                **kwargs,
            )
            fields[key] = (
                type_hint,
                self._construct_field_info(elem, purpose, dto_field),
            )

        dto = create_model(  # type: ignore[call-overload]
            name,
            __base__=base,
            __module__=getattr(model, "__module__", __name__),
            __validators__=validators,
            __cls_kwargs__={"model": model},
            **fields,
        )
        dto = cast("type[FromMapped[AnyDeclarative]]", dto)

        if name != root_dto_name and forward_refs:
            self._update_forward_refs(dto.__name__)

        return dto  # type: ignore[no-any-return]


pydantic_dto_factory = PydanticDTOFactory()
