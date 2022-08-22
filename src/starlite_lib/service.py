from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from . import repository, schema

T = TypeVar("T")
T_repository = TypeVar("T_repository", bound=repository.Base)
T_schema = TypeVar("T_schema", bound=schema.Base)


class Base(Generic[T_repository, T_schema]):
    """
    Generic service object.

    Parameters
    ----------
    session : AsyncSession
        Users should be careful to call the [`AsyncSession.close()`][sqlalchemy.ext.asyncio.AsyncSession.close]
        method once service object no longer needed.
    id_ : Any, optional
        ID of specific instance that the service object should operate on.
    id_filter : repository.CollectionFilter | None, optional
        Adds an `in_()` filter to narrow the select query to the specific identities.
    created_filter : repository.BeforeAfter | None, optional
        Filter the select query by date/time created.
    updated_filter : repository.BeforeAfter | None, optional
        Filter the select query by date/time updated.
    limit_offset : repository.LimitOffset | None, optional
        Apply limit/offset pagination to the select query.
    exclude_keys : set[str] | None
        Keys to be excluded from inbound serialized data passed to the repository.
    **kwargs : Any
        Filter the select query with arbitrary key/value pairs.
    """

    repository_type: type[T_repository]
    """A [`repository.Base`][starlite_lib.repository.Base] concrete subclass."""
    schema_type: type[T_schema]
    """A [`schema.Base`][starlite_lib.schema.Base] concrete subclass."""
    exclude_keys = {"created", "updated"}
    """
    These keys are always excluded from payloads passed to the repository. Merged with the 
    `exclude_keys` parameter on instantiation.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        id_: Any | None = None,
        id_filter: repository.CollectionFilter | None = None,
        created_filter: repository.BeforeAfter | None = None,
        updated_filter: repository.BeforeAfter | None = None,
        limit_offset: repository.LimitOffset | None = None,
        exclude_keys: set[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.repository = self.repository_type(
            session=session,
            id_=id_,
            id_filter=id_filter,
            created_filter=created_filter,
            updated_filter=updated_filter,
            limit_offset=limit_offset,
            **kwargs,
        )
        self.id = id_
        if exclude_keys is not None:
            self.exclude_keys = self.exclude_keys.union(exclude_keys)

    async def commit(self) -> None:
        """
        Convenience method to commit the underlying repository session.
        """
        await self.repository.commit()

    async def rollback(self) -> None:
        """
        Convenience method to roll back the underlying repository session.
        """
        await self.repository.rollback()

    def serialize(self, data: T_schema) -> dict[str, Any]:
        """
        Convert `data` that is a pydantic model instance to a `dict`.

        Handles exclusion of attribs that should not be able to be updated given current context.

        Parameters
        ----------
        data : T_schema
            A pydantic model instance.

        Returns
        -------
        dict[str, Any]
            Serialized representation of `data`.
        """
        return data.dict(exclude=self.exclude_keys)

    async def create(self, data: T_schema) -> T_schema:
        """
        Wraps repository instance creation.

        Parameters
        ----------
        data : T_schema
            Representation to be created.

        Returns
        -------
        T_schema
            Representation of created instance.
        """
        model = await self.repository.create(self.serialize(data))
        return self.schema_type.from_orm(model)

    async def list(self) -> list[T_schema]:
        """
        Wraps repository scalars operation.

        Returns
        -------
        list[T_schema]
            Return value of `self.repository.scalars()` parsed to `T_schema`.
        """
        models = await self.repository.scalars()
        return [self.schema_type.from_orm(i) for i in models]

    async def update(self, data: T_schema) -> T_schema:
        """
        Wraps repository update operation.

        Parameters
        ----------
        data : T_schema
            Representation to be updated.

        Returns
        -------
        T_schema
            Refreshed after insert.
        """
        model = await self.repository.update(self.serialize(data))
        return self.schema_type.from_orm(model)

    async def upsert(self, data: T_schema) -> T_schema:
        """
        Wraps repository upsert operation.

        Parameters
        ----------
        data : T_schema
            Representation for upsert.

        Returns
        -------
        T_schema
            Refreshed after insert.
        """
        model = await self.repository.upsert(self.serialize(data))
        return self.schema_type.from_orm(model)

    async def show(self) -> T_schema:
        """
        Wraps repository scalar operation.

        This method will throw an exception if the query hasn't been filtered to only return one
        instance before calling.

        Returns
        -------
        T_schema
            Representation of instance.
        """
        model = await self.repository.scalar()
        return self.schema_type.from_orm(model)

    async def destroy(self) -> T_schema:
        """
        Wraps repository delete operation.

        Will raise an exception if the query hasn't been filtered to only return one instance before
        calling.

        Returns
        -------
        T_schema
            Representation of the deleted instance.
        """
        model = await self.repository.delete()
        return self.schema_type.from_orm(model)
