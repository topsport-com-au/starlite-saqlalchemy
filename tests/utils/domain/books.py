"""Books domain definitions."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from starlite_saqlalchemy import db, dto, service
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository
from tests.utils.domain.authors import Author


class Book(db.orm.Base):  # pylint: disable=too-few-public-methods
    """The Book domain object."""

    title: Mapped[str]
    author_id: Mapped[UUID] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(
        lazy="joined", innerjoin=True, info={"dto": dto.DTOField(mark=dto.Mark.READ_ONLY)}
    )


class Repository(SQLAlchemyRepository[Book]):
    """Book repository."""

    model_type = Book


class Service(service.Service[Book]):
    """Book service."""

    repository_type = Repository


ReadDTO = dto.FromMapped[Annotated[Book, "read"]]
"""
A pydantic model to serialize outbound `Book` representations.
"""
WriteDTO = dto.FromMapped[Annotated[Book, "write"]]
"""
A pydantic model to validate and deserialize `Book` creation/update data.
"""
