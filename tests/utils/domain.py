"""Example domain objects for testing."""
from __future__ import annotations

from datetime import date  # noqa: TC003

from sqlalchemy.orm import Mapped

from starlite_saqlalchemy import db, dto, service


class Author(db.orm.Base):  # pylint: disable=too-few-public-methods
    """The Author domain object."""

    name: Mapped[str]
    dob: Mapped[date]


Service = service.Service[Author]
"""Author service object."""

CreateDTO = dto.factory("AuthorCreateDTO", Author, purpose=dto.Purpose.WRITE, exclude={"id"})
"""
A pydantic model to validate `Author` creation data.
"""
ReadDTO = dto.factory("AuthorReadDTO", Author, purpose=dto.Purpose.READ)
"""
A pydantic model to serialize outbound `Author` representations.
"""
UpdateDTO = dto.factory("AuthorUpdateDTO", Author, purpose=dto.Purpose.WRITE)
"""
A pydantic model to validate and deserialize `Author` update data.
"""
