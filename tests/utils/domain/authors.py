"""Example domain objects for testing."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from sqlalchemy.orm import Mapped

from starlite_saqlalchemy import db, dto
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository
from starlite_saqlalchemy.service.sqlalchemy import RepositoryService


class Author(db.orm.Base):
    """The Author domain object."""

    name: Mapped[str]
    dob: Mapped[date]


class Repository(SQLAlchemyRepository[Author]):
    """Author repository."""

    model_type = Author


class Service(RepositoryService[Author]):
    """Author service object."""

    repository_type = Repository


ReadDTO = dto.FromMapped[Annotated[Author, "read"]]
"""A pydantic model to serialize outbound `Author` representations."""

WriteDTO = dto.FromMapped[Annotated[Author, "write"]]
"""A pydantic model to validate and deserialize `Author` update data."""
