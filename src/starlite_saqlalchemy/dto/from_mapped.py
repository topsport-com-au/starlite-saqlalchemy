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

from sqlalchemy import Column, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, RelationshipProperty, registry

from starlite_saqlalchemy import settings

from .types import DTOField, Mark, Purpose

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, TypeAlias

    from sqlalchemy.orm import Mapper
    from sqlalchemy.sql.base import ReadOnlyColumnCollection
    from sqlalchemy.util import ReadOnlyProperties

    Registry: TypeAlias = registry


__all__ = ("FromMappedBase", "DTOFactory")

AnyDeclarative = TypeVar("AnyDeclarative", bound=DeclarativeBase)
DTO = TypeVar("DTO")


class FromMappedBase(Generic[DTO, AnyDeclarative]):
    """Base class to define DTO mapping classes."""

    __sqla_model__: ClassVar[type[DeclarativeBase]]

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

    @classmethod
    def _factory(
        cls,
        name: str,
        model: type[AnyDeclarative],
        purpose: Purpose,
        exclude: set[str],
    ) -> type[FromMappedBase[DTO, AnyDeclarative]]:
        raise NotImplementedError


class DTOFactory(Generic[DTO]):
    """Base class for implementing DTO facory.

    Provide methods to inspect SQLAlchemy models and iterating over
    fields to convert.
    """

    def __init__(self, reg: Registry | None = None) -> None:
        """Initialize internal state to keep track of generated DTOs."""
        self._mapped_classes: dict[str, type[DeclarativeBase]] | None = None
        self._registries: list[Registry] = []
        if reg:
            self._registries.append(reg)
        self._model_modules: set[ModuleType] = set()
        # Mapping of all existing dtos names to their class, both declared and generated
        self.dtos: dict[str, type[FromMappedBase]] = {}
        # Mapping of sqla models to their DTO, both declared and generated
        self.model_dtos: dict[type[DeclarativeBase], type[FromMappedBase]] = {}
        # DTO's children. Used to update forwardrefs of generated dtos
        self.dto_children: dict[str, list[type[FromMappedBase]]] = defaultdict(list)

    def _inspect_model(
        self, model: type[DeclarativeBase]
    ) -> tuple[ReadOnlyColumnCollection[str, Column], ReadOnlyProperties[RelationshipProperty]]:
        """Inspect the given SQLAlchemy model.

        Args:
            model: The SQLAlchemy model to inspect

        Return:
            columns and relationships for the given model
        """
        mapper = cast("Mapper", inspect(model))
        columns = mapper.columns
        relationships = mapper.relationships
        return columns, relationships

    def _get_localns(self, model: type[DeclarativeBase]) -> dict[str, Any]:
        """Build namespace for resolving forward refs of the given model.

        Args:
            model: The SQLAlchemy model for which to build the namespace

        Returns:
            A dict suitable to pass to `get_type_hints`
            to resolve forward refs of the given model
        """
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
        """Whether the model field should be excluded from the dto or not."""
        if elem.key in exclude:
            return True
        if dto_attrib.mark is Mark.PRIVATE:
            return True
        if purpose is Purpose.WRITE and dto_attrib.mark is Mark.READ_ONLY:
            return True
        return False

    def _resolve_type(
        self,
        elem: Column | RelationshipProperty,
        type_hint: Any,
        name: str,
        purpose: Purpose,
        parents: defaultdict[Column | RelationshipProperty, set[type[AnyDeclarative]]],
        forward_refs: defaultdict[type[DeclarativeBase], set[str]],
        level: int,
        root: Column | RelationshipProperty,
        **kwargs: Any,
    ) -> Any:
        """Recursively resolve the type hint to a valid pydantic type.

        Args:
            elem: The column or relationship associated with the type hint
            type_hint: Type hint to resolve
            name: The name of the DTO that is being generated
            purpose: DTO purpose
            parents: Dependency chain of the current SQAlchemy model
            forward_refs: Forward refs that have been found when generating the DTO
            level: Indicate recursion level when resolving model children
            root: The root model's column that led to resolving the current type

        Returns:
            unchanged `type_hint` if `elem` is not a relationship,
            else a new type hint referencing a DTO generated after the relationship
        """
        if not isinstance(elem, RelationshipProperty):
            return type_hint
        model = elem.mapper.class_
        dto_name = f"{name}_{model.__name__}"
        dto: Any
        if model in self.model_dtos:
            dto = self.model_dtos[model]
        elif len(parents[root]) > 1 and model in parents[root]:
            forward_refs[model].add(dto_name)
            dto = ForwardRef(dto_name)
        else:
            level += 1
            parents[root].add(model)
            dto = self.factory(
                name=dto_name,
                model=model,
                purpose=purpose,
                _forward_refs=forward_refs,
                _parents=parents,
                _level=level,
                _root=root,
                **kwargs,
            )
        if elem.uselist:
            dto = list[dto]
        if self.is_type_hint_optional(type_hint):
            return Optional[dto]
        return dto

    def _factory(
        self,
        name: str,
        root_dto_name: str | None,
        model: type[AnyDeclarative],
        purpose: Purpose,
        base: type[DTO] | None,
        exclude: set[str],
        parents: defaultdict[Column | RelationshipProperty, set[type[AnyDeclarative]]],
        forward_refs: defaultdict[type[DeclarativeBase], set[str]],
        level: int = 0,
        root: Column | RelationshipProperty | None = None,
        **kwargs: Any,
    ) -> type[FromMappedBase[DTO, AnyDeclarative]]:
        """Build a Data transfer object (DTO) from an SQAlchemy model.

        This inner factory is invoked by the public factory() method

        Args:
            name: Current DTO name
            root_dto_name: The DTO name when factory() was first called
            model: SQLAlchemy model from which to generate the DTO
            purpose: DTO purpose
            parents: Dependency chain of the current SQAlchemy model
            forward_refs: Forward refs that have been found when generating the DTO
            level: Indicate recursion level when resolving model children
            root: The root model's column that led to resolving the current type


        Returns:
            A DTO generated after the given model.
        """
        raise NotImplementedError

    @property
    def mapped_classes(self) -> dict[str, type[DeclarativeBase]]:
        """Get mapped classes across all added registries.

        Returns:
            A mapping of class name -> SQLAlchemy mapped class.
        """
        if self._mapped_classes is None:
            self._mapped_classes = {}
            for reg in self._registries:
                self._mapped_classes.update(
                    {m.class_.__name__: m.class_ for m in list(reg.mappers)}
                )
        return self._mapped_classes

    def add_registry(self, reg: Registry) -> None:
        """Add a registry from which mapped classes can be used to generate
        dtos.

        Args:
            reg: The registry to add
        """
        self._registries.append(reg)

    def clear_mapped_classes(self) -> None:
        """Clear mapping of known mapped classes and registry list.

        After calling this method, the factory will not be able resolve
        forward refs when generating dtos.
        """
        self._registries = []
        self._mapped_classes = None

    def get_dto_field(self, elem: Column | RelationshipProperty) -> DTOField:
        """Return the DTOField from the given Column or relationship.

        Args:
            elem: The models column or relationship from which to retrieve the DTOField.

        Returns:
            The DTOField associated with `elem`
        """
        return elem.info.get(settings.api.DTO_INFO_KEY, DTOField())

    def is_type_hint_optional(self, type_hint: Any) -> bool:
        """Whether the given type hint is considered as optional or not.

        Returns:
            `True` if arguments of the given type hint are optional

        Three cases are considered:
        ```
            Optional[str]
            Union[str, None]
            str | None
        ```
        In any other form, the type hint will not be considered as optional
        """
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
        self,
        model: type[DeclarativeBase],
        purpose: Purpose,
        exclude: set[str],
        level: int,
        root: Column | RelationshipProperty | None,
    ) -> Generator[
        tuple[str, Any, Column | RelationshipProperty, Column | RelationshipProperty, int],
        None,
        None,
    ]:
        """Iterate over type hints of columns and relationships for the given
        model.

        Args:
            model: The model from which to retrieve type hints
            purpose: DTO purpose
            exclude: Set of field names that should be excluded from the DTO
            level: Indicate recursion level when resolving model children
            root: The root model's column that led to resolving the current type

        Yields:
            A tuple of (Attribute name, type hint, column/relationship, root, level)
        """
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

            # Only update the root parent when iterating on the root model fields
            if root is None or level == 0:
                root = elem

            yield key, type_hint, elem, root, level

    def factory(
        self,
        name: str,
        model: type[AnyDeclarative],
        purpose: Purpose,
        base: type[DTO] | None = None,
        exclude: set[str] | None = None,
        _parents: defaultdict[Column | RelationshipProperty, set[type[AnyDeclarative]]]
        | None = None,
        _forward_refs: defaultdict[type[DeclarativeBase], set[str]] | None = None,
        _level: int = 0,
        _root: Column | RelationshipProperty | None = None,
        **kwargs: Any,
    ) -> type[FromMappedBase[DTO, AnyDeclarative]]:
        """Build a Data transfer object (DTO) from an SQAlchemy model.

        Args:
            name: DTO name
            model: SQLAlchemy model from which to generate the DTO
            purpose: DTO purpose
            base: Class to use as base when generating the model
            exclude: Set of field names that should be excluded from the DTO

        Returns:
            _description_
        """
        exclude = set() if exclude is None else exclude
        root_dto_name: str | None = None
        if _parents is None:
            root_dto_name = name
            _parents = defaultdict(set)
        if _forward_refs is None:
            _forward_refs = defaultdict(set)

        dto = self._factory(
            name=name,
            root_dto_name=root_dto_name,
            model=model,
            purpose=purpose,
            base=base,
            exclude=exclude,
            parents=_parents,
            forward_refs=_forward_refs,
            level=_level,
            root=_root,
            **kwargs,
        )

        self.dtos[name] = dto
        self.model_dtos[model] = dto

        if model_forward_refs := _forward_refs.get(model):
            for forward_ref in model_forward_refs:
                self.dtos[forward_ref] = dto
        if name != root_dto_name and root_dto_name is not None:
            self.dto_children[root_dto_name].append(dto)

        return dto
