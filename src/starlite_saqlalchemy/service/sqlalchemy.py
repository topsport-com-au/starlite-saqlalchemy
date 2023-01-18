"""Service object implementation for SQLAlchemy.

RepositoryService object is generic on the domain model type which
should be a SQLAlchemy model.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from starlite_saqlalchemy.db import async_session_factory
from starlite_saqlalchemy.repository.sqlalchemy import ModelT

from .generic import Service

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from starlite_saqlalchemy.repository.abc import AbstractRepository
    from starlite_saqlalchemy.repository.types import FilterTypes


RepoServiceT = TypeVar("RepoServiceT", bound="RepositoryService")


class RepositoryService(Service[ModelT], Generic[ModelT]):
    """Service object that operates on a repository object."""

    __id__ = "starlite_saqlalchemy.service.sqlalchemy.RepositoryService"

    repository_type: type[AbstractRepository[ModelT]]

    def __init__(self, **repo_kwargs: Any) -> None:
        """Configure the service object.

        Args:
            **repo_kwargs: passed as keyword args to repo instantiation.
        """
        self.repository = self.repository_type(**repo_kwargs)

    async def create(self, data: ModelT) -> ModelT:
        """Wrap repository instance creation.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return await self.repository.add(data)

    async def list(self, *filters: "FilterTypes", **kwargs: Any) -> list[ModelT]:
        """Wrap repository scalars operation.

        Args:
            *filters: Collection route filters.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        return await self.repository.list(*filters, **kwargs)

    async def update(self, id_: Any, data: ModelT) -> ModelT:
        """Wrap repository update operation.

        Args:
            id_: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        self.repository.set_id_attribute_value(id_, data)
        return await self.repository.update(data)

    async def upsert(self, id_: Any, data: ModelT) -> ModelT:
        """Wrap repository upsert operation.

        Args:
            id_: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        self.repository.set_id_attribute_value(id_, data)
        return await self.repository.upsert(data)

    async def get(self, id_: Any) -> ModelT:
        """Wrap repository scalar operation.

        Args:
            id_: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `id_`.
        """
        return await self.repository.get(id_)

    async def delete(self, id_: Any) -> ModelT:
        """Wrap repository delete operation.

        Args:
            id_: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        return await self.repository.delete(id_)

    @classmethod
    @contextlib.asynccontextmanager
    async def new(cls: type[RepoServiceT]) -> AsyncIterator[RepoServiceT]:
        """Context manager that returns instance of service object.

        Handles construction of the database session.

        Returns:
            The service object instance.
        """
        async with async_session_factory() as session:
            yield cls(session=session)
