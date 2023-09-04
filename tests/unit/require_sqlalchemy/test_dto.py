"""Tests for the dto factory."""  # noqa: FA100
# pylint: disable=missing-class-docstring,invalid-name

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Union, get_args, get_origin
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, Field, constr, validator
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from starlite_saqlalchemy import dto, settings
from starlite_saqlalchemy.db import orm
from tests.utils.domain.authors import Author, WriteDTO

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from sqlalchemy.engine.default import DefaultExecutionContext


def test_model_write_dto(raw_authors: list[dict[str, Any]]) -> None:
    """Create a model from DTO instance and check the values on the model."""
    dto_type = dto.FromMapped[Annotated[Author, dto.config("write")]]
    assert dto_type.__fields__.keys() == {"name", "dob"}
    inst = dto_type(**raw_authors[0])
    model = Author(**inst.dict(exclude_unset=True))
    assert {k: v for k, v in model.__dict__.items() if not k.startswith("_")} == {
        "name": "Agatha Christie",
        "dob": date(1890, 9, 15),
    }


def test_model_read_dto(raw_authors: list[dict[str, Any]]) -> None:
    """Create a model from DTO instance and check the values on the model."""
    dto_type = dto.FromMapped[Annotated[Author, dto.config("read")]]
    assert dto_type.__fields__.keys() == {"name", "dob", "id", "created", "updated"}
    inst = dto_type(**raw_authors[1])
    model = Author(**inst.dict(exclude_unset=True))
    assert {k: v for k, v in model.__dict__.items() if not k.startswith("_")} == {
        "name": "Leo Tolstoy",
        "dob": date(1828, 9, 9),
        "id": UUID("5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"),
        "updated": datetime(1, 1, 1, 0, 0),
        "created": datetime(1, 1, 1, 0, 0),
    }


def test_dto_exclude() -> None:
    """Test that names in `exclude` are not included in DTO."""
    dto_type = dto.FromMapped[Annotated[Author, dto.config("read", {"id"})]]
    assert dto_type.__fields__.keys() == {"name", "dob", "created", "updated"}


@pytest.mark.parametrize(
    ("purpose", "default", "exp"), [(dto.Purpose.WRITE, 3, 3), (dto.Purpose.READ, 3, None)]
)
def test_write_dto_for_model_field_scalar_default(
    purpose: dto.Purpose, default: Any, exp: Any
) -> None:
    """Test DTO scalar defaults for write and read purposes."""

    class Model(orm.Base):
        field: Mapped[int] = mapped_column(default=default)

    dto_model = dto.FromMapped[Annotated[Model, dto.config(purpose)]]
    assert dto_model.__fields__["field"].default == exp


def test_write_dto_for_model_field_factory_default() -> None:
    """Test write purposed DTO includes the default factory."""

    class Model(orm.Base):
        field: Mapped[UUID] = mapped_column(default=uuid4)

    dto_model = dto.FromMapped[Annotated[Model, dto.config("write")]]
    assert dto_model.__fields__["field"].default_factory is not None
    assert isinstance(dto_model.__fields__["field"].default_factory(), UUID)


def test_read_dto_for_model_field_factory_default() -> None:
    """Test read purposed DTO excludes the default factory."""

    class Model(orm.Base):
        field: Mapped[UUID] = mapped_column(default=uuid4)

    dto_model = dto.FromMapped[Annotated[Model, dto.config("read")]]
    assert dto_model.__fields__["field"].default_factory is None


def test_write_dto_for_custom_default_callable_with_context() -> None:
    """Test column with default callable that accepts context arg."""

    def my_context(context: "DefaultExecutionContext") -> int:
        return context.get_current_parameters()["a"] + 1  # type: ignore

    class A(orm.Base):
        a: Mapped[int]
        a_plus: Mapped[int] = mapped_column(default=my_context)

    DTO = dto.FromMapped[Annotated[A, "write"]]
    field = DTO.__fields__["a_plus"]
    assert field.required
    assert field.default is None


def test_write_dto_for_custom_default_callable_staticmethod() -> None:
    """Test column with a static method as default callable."""

    class A(orm.Base):
        @staticmethod
        def my_context() -> int:
            return 42

        a: Mapped[int]
        a_plus: Mapped[int] = mapped_column(default=my_context)

    DTO = dto.FromMapped[Annotated[A, "write"]]
    field = DTO.__fields__["a_plus"]
    assert not field.required
    assert field.default is None
    dto_instance = DTO.parse_obj({"a": 1})
    assert getattr(dto_instance, "a_plus") == 42  # noqa: B009


def test_read_dto_for_model_field_unsupported_default() -> None:
    """Test for error condition where we don't know what to do with a default
    type."""

    class Model(orm.Base):
        field: Mapped[datetime] = mapped_column(default=func.now())

    with pytest.raises(ValueError):  # noqa: PT011
        # noinspection PyStatementEffect
        dto.FromMapped[  # pylint: disable=expression-not-assigned
            Annotated[Model, dto.config("write")]
        ]


@pytest.mark.parametrize("purpose", [dto.Purpose.WRITE, dto.Purpose.READ])
def test_dto_for_private_model_field(purpose: dto.Purpose) -> None:
    """Ensure that fields markets as PRIVATE are excluded from DTO."""

    class Model(orm.Base):
        field: Mapped[datetime] = mapped_column(
            default=datetime.now(),
            info={settings.api.DTO_INFO_KEY: dto.DTOField(mark=dto.Mark.PRIVATE)},
        )

    dto_model = dto.FromMapped[Annotated[Model, dto.config(purpose)]]
    assert "field" not in dto_model.__fields__


@pytest.mark.parametrize("purpose", [dto.Purpose.WRITE, dto.Purpose.READ])
def test_dto_for_non_mapped_model_field(purpose: dto.Purpose) -> None:
    """Ensure that we exclude unmapped fields from DTOs."""

    class Model(orm.Base):
        field: ClassVar[datetime]

    dto_model = dto.FromMapped[Annotated[Model, dto.config(purpose)]]
    assert "field" not in dto_model.__fields__


def test_dto_factory_forward_ref_annotations(create_module: "Callable[[str], ModuleType]") -> None:
    """Test that dto generated from module with forward ref annotations
    works."""
    module = create_module(
        """
from __future__ import annotations
from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlite_saqlalchemy.db import orm

class Related(orm.Base):
    test_id: Mapped[UUID] = mapped_column(ForeignKey("test.id"))

class Test(orm.Base):
    hello: Mapped[str]
    related: Mapped[Related] = relationship()
"""
    )
    model = module.Test
    assert all(isinstance(model.__annotations__[k], str) for k in ("hello", "related"))
    dto_model = dto.FromMapped[Annotated[model, dto.config("read")]]
    assert all(not isinstance(dto_model.__annotations__[k], str) for k in ("hello", "related"))


def test_subclassed_dto() -> None:
    """Test dto subclass decoration.

    Test ensures that fields defined on the subclass overwrite those
    generated by factory(), that fields not defined on the subclass are
    added to the DTO, and that validators work for fields that are added
    both statically, and dynamically (with the `check_fields=False`
    flag).
    """

    class AuthorDTO(dto.FromMapped[Annotated[Author, "write"]]):
        name: constr(to_upper=True)  # pyright:ignore

        @validator("name")
        def validate_name(cls, val: str) -> str:
            """We're shouting!"""
            return f"{val}!"

        @validator("dob", check_fields=False)
        def validate_dob(cls, val: date) -> date:
            """Off by one."""
            val += timedelta(days=1)
            return val

    assert AuthorDTO.parse_obj({"name": "Bill Bryson", "dob": "1951-12-08"}).dict() == {
        "name": "BILL BRYSON!",
        "dob": date(1951, 12, 9),
    }


def test_dto_attrib_validator() -> None:
    """Test arbitrary single arg callables as validators."""

    validator_called = False

    def validate_datetime(val: datetime) -> datetime:
        nonlocal validator_called
        validator_called = True
        return val

    class Model(orm.Base):
        field: Mapped[datetime] = mapped_column(
            info={settings.api.DTO_INFO_KEY: dto.DTOField(validators=[validate_datetime])}
        )

    dto_model = dto.FromMapped[Annotated[Model, dto.config("write")]]
    dto_model.parse_obj({"id": 1, "field": datetime.min})
    assert validator_called


def test_dto_attrib_pydantic_type() -> None:
    """Test declare pydantic type on `dto.DTOField`."""

    class Model(orm.Base):
        field: Mapped[str] = mapped_column(
            info={settings.api.DTO_INFO_KEY: dto.DTOField(pydantic_type=constr(to_upper=True))}
        )

    dto_model = dto.FromMapped[Annotated[Model, dto.config("write")]]
    assert dto_model.parse_obj({"id": 1, "field": "lower"}).dict() == {"field": "LOWER"}


def test_dto_mapped_as_dataclass_model_type() -> None:
    """Test declare pydantic type on `dto.DTOField`."""

    class Model(orm.Base, MappedAsDataclass):
        clz_var: ClassVar[str]
        field: Mapped[str]

    dto_model = dto.FromMapped[Annotated[Model, dto.config("write")]]
    assert dto_model.__fields__.keys() == {"field"}


def test_from_dto() -> None:
    """Test conversion of a DTO instance to a model instance."""
    data = WriteDTO.parse_obj({"name": "someone", "dob": "1982-03-22"})
    author = data.to_mapped()
    assert author.name == "someone"
    assert author.dob == date(1982, 3, 22)


def test_invalid_from_mapped_annotation() -> None:
    """Test error raised if from mapped called without Annotated."""
    with pytest.raises(ValueError):  # noqa:PT011
        dto.FromMapped[Author]  # pylint: disable=pointless-statement


def test_to_mapped_model_with_collection_relationship() -> None:
    """Test building a DTO with collection relationship, and parsing data."""

    class A(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))

    class B(orm.Base):
        a: Mapped[list[A]] = relationship("A")

    DTO = dto.FromMapped[Annotated[B, "write"]]
    dto_instance = DTO.parse_obj({"id": 1, "a": [{"id": 2, "b_id": 1}, {"id": 3, "b_id": 1}]})
    mapped_instance = dto_instance.to_mapped()
    assert len(mapped_instance.a) == 2
    assert all(isinstance(val, A) for val in mapped_instance.a)


def test_to_mapped_model_with_collection_relationship_default() -> None:
    """Test default value of DTO with collection relationship."""

    class A(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))

    class B(orm.Base):
        a: Mapped[list[A]] = relationship("A")

    DTO = dto.FromMapped[Annotated[B, "write"]]
    dto_instance = DTO.parse_obj({"id": 1})
    mapped_instance = dto_instance.to_mapped()
    assert isinstance(mapped_instance.a, list)
    assert len(mapped_instance.a) == 0


def test_to_mapped_model_with_collection_relationship_optional() -> None:
    """Test collection relationship typed as optional."""

    class A(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))

    class B(orm.Base):
        a: Mapped[list[A] | None] = relationship("A")

    DTO = dto.FromMapped[Annotated[B, "write"]]
    assert get_origin(DTO.__fields__["a"].annotation) is Union
    assert type(None) in get_args(DTO.__fields__["a"].annotation)


def test_to_mapped_model_with_scalar_relationship() -> None:
    """Test building DTO with Scalar relationship, and parsing data."""

    class A(orm.Base):
        ...

    class B(orm.Base):
        a_id: Mapped[int] = mapped_column(ForeignKey("a.id"), info=dto.field("private"))
        a: Mapped[A] = relationship("A")

    DTO = dto.FromMapped[Annotated[B, "write"]]
    dto_instance = DTO.parse_obj({"id": 2, "a": {"id": 1}})
    mapped_instance = dto_instance.to_mapped()
    assert isinstance(mapped_instance.a, A)


def test_to_mapped_model_with_scalar_relationship_optional() -> None:
    """Test relationship typed as optional."""

    class A(orm.Base):
        ...

    class B(orm.Base):
        a_id: Mapped[int] = mapped_column(ForeignKey("a.id"), info=dto.field("private"))
        a: Mapped[A | None] = relationship("A")

    DTO = dto.FromMapped[Annotated[B, "write"]]
    assert get_origin(DTO.__fields__["a"].annotation) is Union
    assert type(None) in get_args(DTO.__fields__["a"].annotation)


def test_dto_field_pydantic_field() -> None:
    """Test specifying DTOField.pydantic_field."""

    class A(orm.Base):
        val: Mapped[int] = mapped_column(info=dto.field(pydantic_field=Field(le=1)))

    DTO = dto.FromMapped[Annotated[A, "write"]]
    with pytest.raises(ValueError):  # noqa:PT011
        DTO.parse_obj({"id": 1, "val": 2})


def test_dto_mapped_union() -> None:
    """Test where a column type declared as e.g., `Mapped[str | None]`."""

    class A(orm.Base):
        val: Mapped[str | None]

    DTO = dto.FromMapped[Annotated[A, "write"]]
    field = DTO.__fields__["val"]
    assert field.allow_none is True
    assert field.default is None
    assert field.type_ is str


def test_dto_mapped_union_relationship() -> None:
    """Test where a related type declared as e.g., `Mapped[A | None]`."""

    class A(orm.Base):
        val: Mapped[str | None]

    class B(orm.Base):
        a_id: Mapped[int | None] = mapped_column(ForeignKey("a.id"), info=dto.field("private"))
        a: Mapped[A | None] = relationship(A)

    DTO = dto.FromMapped[Annotated[B, "write"]]
    field = DTO.__fields__["a"]
    assert field.allow_none is True
    assert field.default is None
    assert issubclass(field.type_, BaseModel)
    assert "val" in field.type_.__fields__


def test_dto_string_annotations() -> None:
    """Test model with column using string type annotations."""

    class A(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))
        b: Mapped["B"] = relationship("B")  # noqa: F821

    class B(orm.Base):
        name: Mapped[str]

    dto_model_child = dto.FromMapped[Annotated[A, "write"]]

    dto_child_instance = dto_model_child.parse_obj(
        {
            "id": 1,
            "b_id": 1,
            "b": {"id": 1, "name": "foo"},
        }
    )
    mapped_a_instance = dto_child_instance.to_mapped()
    assert isinstance(mapped_a_instance, A)
    assert isinstance(mapped_a_instance.b, B)


def test_dto_references_cycle() -> None:
    """Test a simple reference cycle."""

    class A(orm.Base):
        name: Mapped[str]
        children: Mapped[list["B"] | None] = relationship("B", back_populates="a")  # noqa: F821

    class B(orm.Base):
        name: Mapped[str]
        a_id: Mapped[int] = mapped_column(ForeignKey("a.id"))
        a: Mapped["A"] = relationship("A", back_populates="children")

    dto_model_child = dto.FromMapped[Annotated[B, "write"]]

    dto_child_instance = dto_model_child.parse_obj(
        {"id": 1, "name": "b", "a_id": 1, "a": {"id": 1, "name": "a"}}
    )
    mapped_child_instance = dto_child_instance.to_mapped()
    assert isinstance(mapped_child_instance, B)
    assert isinstance(mapped_child_instance.a, A)


def test_dto_references_inner_cycle() -> None:
    """Test a reference cycle that do not start in the first SQLAlchemy
    model."""

    class A(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))
        b: Mapped["B"] = relationship("B")  # noqa: F821

    class B(orm.Base):
        children: Mapped[list["C"]] = relationship("C", back_populates="b")  # noqa: F821

    class C(orm.Base):
        b_id: Mapped[int] = mapped_column(ForeignKey("b.id"))
        b: Mapped["B"] = relationship("B", back_populates="children")

    dto_model_child = dto.FromMapped[Annotated[A, "write"]]

    dto_child_instance = dto_model_child.parse_obj(
        {
            "id": 1,
            "b_id": 1,
            "b": {"id": 1, "children": [{"id": 1, "b_id": 1}, {"id": 2, "b_id": 1}]},
        }
    )
    mapped_a_instance = dto_child_instance.to_mapped()
    assert isinstance(mapped_a_instance, A)
    assert isinstance(mapped_a_instance.b, B)
    assert all(isinstance(child, C) for child in mapped_a_instance.b.children)
