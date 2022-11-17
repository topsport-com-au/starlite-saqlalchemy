"""Tests for the dto factory."""
# pylint: disable=redefined-outer-name,too-few-public-methods,missing-class-docstring
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from starlite_saqlalchemy import dto, settings
from tests.utils.domain import Author

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


@pytest.fixture()
def base() -> type[DeclarativeBase]:
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
