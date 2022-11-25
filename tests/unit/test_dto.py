"""Tests for the dto factory."""
# pylint: disable=missing-class-docstring
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, constr, validator
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from starlite_saqlalchemy import dto, settings
from tests.utils.domain import Author, CreateDTO

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


def test_model_write_dto(raw_authors: list[dict[str, Any]]) -> None:
    """Create a model from DTO instance and check the values on the model."""
    dto_type = dto.factory("AuthorDTO", Author, dto.Purpose.WRITE)
    assert dto_type.__fields__.keys() == {"name", "dob"}
    inst = dto_type(**raw_authors[0])
    model = Author(**inst.dict(exclude_unset=True))
    assert {k: v for k, v in model.__dict__.items() if not k.startswith("_")} == {
        "name": "Agatha Christie",
        "dob": date(1890, 9, 15),
    }


def test_model_read_dto(raw_authors: list[dict[str, Any]]) -> None:
    """Create a model from DTO instance and check the values on the model."""
    dto_type = dto.factory("AuthorDTO", Author, dto.Purpose.READ)
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
    dto_type = dto.factory("AuthorDTO", Author, dto.Purpose.READ, exclude={"id"})
    assert dto_type.__fields__.keys() == {"name", "dob", "created", "updated"}


@pytest.fixture(name="base")
def fx_base() -> type[DeclarativeBase]:
    """Declarative base for test models.

    Need a new base for every test, otherwise will get errors to do with
    tables already existing in the mapper when we reuse models of the
    same name across multiple tests.
    """

    class Base(DeclarativeBase):
        id: Mapped[int] = mapped_column(primary_key=True)

    return Base


@pytest.mark.parametrize(
    ("purpose", "default", "exp"), [(dto.Purpose.WRITE, 3, 3), (dto.Purpose.READ, 3, None)]
)
def test_write_dto_for_model_field_scalar_default(
    purpose: dto.Purpose, default: Any, exp: Any, base: type[DeclarativeBase]
) -> None:
    """Test DTO scalar defaults for write and read purposes."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[int] = mapped_column(default=default)

    dto_model = dto.factory("DTO", Model, purpose=purpose)
    assert dto_model.__fields__["field"].default == exp


def test_write_dto_for_model_field_factory_default(base: type[DeclarativeBase]) -> None:
    """Test write purposed DTO includes the default factory."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[UUID] = mapped_column(default=uuid4)

    dto_model = dto.factory("DTO", Model, purpose=dto.Purpose.WRITE)

    assert dto_model.__fields__["field"].default_factory is not None
    assert isinstance(dto_model.__fields__["field"].default_factory(), UUID)


def test_read_dto_for_model_field_factory_default(base: type[DeclarativeBase]) -> None:
    """Test read purposed DTO excludes the default factory."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[UUID] = mapped_column(default=uuid4)

    dto_model = dto.factory("DTO", Model, purpose=dto.Purpose.READ)

    assert dto_model.__fields__["field"].default_factory is None


def test_read_dto_for_model_field_unsupported_default(base: type[DeclarativeBase]) -> None:
    """Test for error condition where we don't know what to do with a default
    type."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[datetime] = mapped_column(default=func.now())

    with pytest.raises(ValueError):  # noqa: PT011
        dto.factory("DTO", Model, purpose=dto.Purpose.WRITE)


@pytest.mark.parametrize("purpose", [dto.Purpose.WRITE, dto.Purpose.READ])
def test_dto_for_private_model_field(purpose: dto.Purpose, base: type[DeclarativeBase]) -> None:
    """Ensure that fields markets as SKIP are excluded from DTO."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[datetime] = mapped_column(
            default=datetime.now(),
            info={settings.api.DTO_INFO_KEY: dto.Attrib(mark=dto.Mark.SKIP)},
        )

    dto_model = dto.factory("DTO", Model, purpose=purpose)
    assert "field" not in dto_model.__fields__


@pytest.mark.parametrize("purpose", [dto.Purpose.WRITE, dto.Purpose.READ])
def test_dto_for_non_mapped_model_field(purpose: dto.Purpose, base: type[DeclarativeBase]) -> None:
    """Ensure that we exclude unmapped fields from DTOs."""

    class Model(base):
        __tablename__ = "smth"
        field: ClassVar[datetime]

    dto_model = dto.factory("DTO", Model, purpose=purpose)
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
    dto_model = dto.factory("TestDTO", module.Test, purpose=dto.Purpose.READ)
    assert all(not isinstance(dto_model.__annotations__[k], str) for k in ("hello", "related"))


def test_dto_decorator() -> None:
    """Test dto decorator.

    Test ensures that fields defined on the decorated class aren't
    overwritten by factory(), that fields not defined on the decorated
    class are added to the DTO, and that validators work for fields that
    are added both statically, and dynamically (with the
    `check_fields=False` flag).
    """

    @dto.decorator(Author, dto.Purpose.WRITE)
    class AuthorDTO(BaseModel):
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


def test_dto_attrib_validator(base: type[DeclarativeBase]) -> None:
    """Test arbitrary single arg callables as validators."""

    validator_called = False

    def validate_datetime(val: datetime) -> datetime:
        nonlocal validator_called
        validator_called = True
        return val

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[datetime] = mapped_column(
            info={settings.api.DTO_INFO_KEY: dto.Attrib(validators=[validate_datetime])}
        )

    dto_model = dto.factory("DTO", Model, purpose=dto.Purpose.WRITE)
    dto_model.parse_obj({"id": 1, "field": datetime.min})
    assert validator_called


def test_dto_attrib_pydantic_type(base: type[DeclarativeBase]) -> None:
    """Test declare pydantic type on `dto.Attrib`."""

    class Model(base):
        __tablename__ = "smth"
        field: Mapped[str] = mapped_column(
            info={settings.api.DTO_INFO_KEY: dto.Attrib(pydantic_type=constr(to_upper=True))}
        )

    dto_model = dto.factory("DTO", Model, purpose=dto.Purpose.WRITE)
    assert dto_model.parse_obj({"id": 1, "field": "lower"}).dict() == {"id": 1, "field": "LOWER"}


def test_dto_mapped_as_dataclass_model_type(base: type[DeclarativeBase]) -> None:
    """Test declare pydantic type on `dto.Attrib`."""

    class Model(MappedAsDataclass, base):
        __tablename__ = "smth"
        clz_var: ClassVar[str]
        field: Mapped[str]

    dto_model = dto.factory("DTO", Model, purpose=dto.Purpose.WRITE)
    assert dto_model.__fields__.keys() == {"id", "field"}


def test_from_dto() -> None:
    """Test conversion of a DTO instance to a model instance."""
    data = CreateDTO.parse_obj({"name": "someone", "dob": "1982-03-22"})
    author = data.to_mapped()
    assert author.name == "someone"
    assert author.dob == date(1982, 3, 22)
