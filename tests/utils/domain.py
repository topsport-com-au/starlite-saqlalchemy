"""Example domain objects for testing."""
from datetime import date  # noqa: TC003

from sqlalchemy.orm import Mapped

from starlite_saqlalchemy import dto, orm, service
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository
from starlite_saqlalchemy.worker import queue


class Author(orm.Base):  # pylint: disable=too-few-public-methods
    """The Author domain object."""

    name: Mapped[str]
    dob: Mapped[date]


class Repository(SQLAlchemyRepository[Author]):
    """Author repository."""

    model_type = Author


class Service(service.Service[Author]):
    """Author service object."""

    repository_type = Repository

    async def create(self, data: Author) -> Author:
        created = await super().create(data)
        await queue.enqueue("author_created", data=ReadDTO.from_orm(created).dict())
        return data


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
