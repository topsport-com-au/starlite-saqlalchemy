"""Example domain objects for testing."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel
from sqlalchemy.orm import Mapped

from starlite_saqlalchemy import db, dto, repository, service


class Author(db.orm.Base):
    """The Author domain object."""

    name: Mapped[str]
    dob: Mapped[date]


class Repository(repository.sqlalchemy.SQLAlchemyRepository[Author]):
    """Author repository."""

    model_type = Author


class Service(service.Service[Author]):
    """Author service object."""

    repository_type = Repository


@dto.decorator(Author, dto.Purpose.WRITE)
class CreateDTO(BaseModel):
    """A pydantic model to validate `Author` creation data."""


ReadDTO = dto.factory("AuthorReadDTO", Author, dto.Purpose.READ)
"""
A pydantic model to serialize outbound `Author` representations.
"""
UpdateDTO = dto.factory("AuthorUpdateDTO", Author, dto.Purpose.WRITE)
"""
A pydantic model to validate and deserialize `Author` update data.
"""
