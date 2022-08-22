from collections import abc
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar, overload
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable
from sqlalchemy.sql.selectable import TypedReturnsRows

from . import orm

__all__ = [
    "BeforeAfter",
    "CollectionFilter",
    "LimitOffset",
    "RepositoryNotFoundException",
    "RepositoryConflictException",
    "RepositoryException",
    "T_base",
    "T_model",
]

T = TypeVar("T")
T_row = TypeVar("T_row", bound=tuple[Any, ...])
T_model = TypeVar("T_model", bound=orm.Base)
T_base = TypeVar("T_base", bound=orm.Base)
T_param = TypeVar("T_param", bound=float | str | UUID)


@dataclass
class BeforeAfter:
    """
    Data required to filter a query on a `datetime` column.
    """

    field_name: str
    """Name of the model attribute to filter on."""
    before: datetime | None
    """Filter results where field earlier than this [datetime][datetime.datetime]"""
    after: datetime | None
    """Filter results where field later than this [datetime][datetime.datetime]"""


@dataclass
class CollectionFilter(Generic[T_param]):
    """
    Data required to construct a `WHERE ... IN (...)` clause.
    """

    field_name: str
    """Name of the model attribute to filter on."""
    values: list[T_param] | None
    """Values for `IN` clause."""


@dataclass
class LimitOffset:
    """
    Data required to add limit/offset filtering to a query.
    """

    limit: int
    """Value for `LIMIT` clause of query."""
    offset: int
    """Value for `OFFSET` clause of query."""


class RepositoryException(Exception):
    """
    Base repository exception type.
    """


class RepositoryConflictException(RepositoryException):
    """
    Wraps integrity error from database layer.
    """


class RepositoryNotFoundException(RepositoryException):
    """
    Raised when a method referencing a specific instance by identity is called and no instance with
    that identity exists.
    """


class Base(Generic[T_model]):
    """
    ABC for Repository objects.

    Filtering for the route must be done as part of the repository construction. For example, if
    accessing `repository.scalar()` accessor method, and more than one result is returned from the
    query, a `RepositoryException` is raised by default (the exception type raised is configurable).

    Attributes
    ----------
    session : AsyncSession
        ORM database connection interface.
    select : Select
        [Select][sqlalchemy.sql.expression.Select] for [`model_type`][starlite_lib.repository.Base.model_type].

    Parameters
    ----------
    session : AsyncSession
        Users should be careful to call the [`AsyncSession.close()`][sqlalchemy.ext.asyncio.AsyncSession.close]
        method once repository no longer needed.
    id_ : UUID | None, optional
        Filter the query for a single identity, by default filtered on attribute named "id" but can
        be configured using the `id_key` parameter.
    id_filter : CollectionFilter[UUID] | None, optional
        Filter the query for a group of identities.
    created_filter : BeforeAfter | None, optional
        Filter the query based on date/time created.
    updated_filter : BeforeAfter | None, optional
        Filter the query based on date/time updated.
    limit_offset : LimitOffset | None, optional
        Apply limit/offset pagination to the query.
    """

    model_type: type[T_model]
    """
    A model that extends [`DeclarativeBase`][sqlalchemy.orm.DeclarativeBase]. Must be set by 
    concrete subclasses.
    """
    id_key: str = "id"
    """
    The name of the attribute on `model_type` used to filter by identity.
    """
    base_error_type: type[Exception] = RepositoryException
    """
    Exception type raised when there is not a more specific error to throw.
    """
    integrity_error_type: type[Exception] = RepositoryConflictException
    """
    Exception type raised when a database layer integrity error is caught.
    """
    not_found_error_type: type[Exception] = RepositoryNotFoundException
    """
    Exception type raised on access to `scalar()`, `update()` and `delete()` methods when the select 
    query returns no rows, default `RepositoryNotFoundException`.
    """

    def __init__(
        self,
        session: AsyncSession,
        id_: UUID | None = None,
        id_filter: CollectionFilter[UUID] | None = None,
        created_filter: BeforeAfter | None = None,
        updated_filter: BeforeAfter | None = None,
        limit_offset: LimitOffset | None = None,
        **kwargs: Any,
    ) -> None:
        self.session = session
        self.select = select(self.model_type)
        if id_:
            kwargs.update({self.id_key: id_})
        self.filter_select_by_kwargs(**kwargs)
        if id_filter:
            self.filter_in_collection(id_filter)
        if created_filter:
            self.filter_on_datetime_field(created_filter)
        if updated_filter:
            self.filter_on_datetime_field(updated_filter)
        if limit_offset:
            self.apply_limit_offset_pagination(limit_offset)

    @contextmanager
    def catch_sqlalchemy_exception(self) -> Any:
        """
        Context manager that raises a custom exception chained from an original
        [`SQLAlchemyError`][sqlalchemy.exc.SQLAlchemyError].

        If [`IntegrityError`][sqlalchemy.exc.IntegrityError] is raised, we raise
        [`Base.integrity_error_type`][starlite_lib.repository.Base.integrity_error_type].

        Any other [`SQLAlchemyError`][sqlalchemy.exc.SQLAlchemyError] is wrapped in
        [`Base.base_error_type`][starlite_lib.repository.Base.base_error_type].
        """
        try:
            yield
        except IntegrityError as e:
            raise self.integrity_error_type from e
        except SQLAlchemyError as e:
            raise self.base_error_type(f"An exception occurred: {e}") from e

    def filter_select_by_kwargs(self, **kwargs: Any) -> None:
        """
        Add a where clause to `self.select` for each key/value pair in `**kwargs` where key should
        be an attribute of `model_type` and value is used for an equality test.

        Parameters
        ----------
        **kwargs : Any
            Keys should be attributes of `model_type`.
        """
        for k, v in kwargs.items():
            self.select = self.select.where(getattr(self.model_type, k) == v)

    @overload
    async def execute(self, statement: TypedReturnsRows[T_row], **kwargs: Any) -> Result[T_row]:
        ...

    @overload
    async def execute(self, statement: Executable, **kwargs: Any) -> Result[Any]:
        ...

    async def execute(self, statement: Executable, **kwargs: Any) -> Result[Any]:
        """
        Execute `statement` with [`self.session`][starlite_lib.repository.Base.session].

        Parameters
        ----------
        statement : Executable
            Any SQLAlchemy executable type.
        **kwargs : Any
            Passed as kwargs to [`self.session.execute()`][sqlalchemy.ext.asyncio.AsyncSession.execute]

        Returns
        -------
        Result
            A set of database results.
        """
        with self.catch_sqlalchemy_exception():
            return await self.session.execute(statement, **kwargs)

    async def add_flush_refresh(self, instance: T_base) -> T_base:
        """
        Adds `instance` to `self.session`, flush changes, refresh `instance`.

        Parameters
        ----------
        instance : T_base
            A sqlalchemy model.

        Returns
        -------
        T_base
            `instance`
        """
        with self.catch_sqlalchemy_exception():
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    # create

    def parse_obj(self, data: abc.Mapping[str, Any]) -> T_model:
        """
        Given a mapping of unstructured data, create an instance of `self.model_type`.

        Parameters
        ----------
        data : Mapping[str, Any]

        Returns
        -------
        T_model
        """
        return self.model_type(**data)

    async def create(self, data: dict[str, Any]) -> T_model:
        """
        Create an instance of type `self.model`, add to session, and flush to db. Does not commit.

        Parameters
        ----------
        data : dict[str, Any]
            Unstructured representation of `T_model`.

        Returns
        -------
        T_model
            A session-attached instance that has been flushed to the database, and refreshed.
        """
        return await self.add_flush_refresh(self.parse_obj(data))

    # read

    def apply_limit_offset_pagination(self, data: LimitOffset) -> None:
        """
        Paginate the base select query.

        Parameters
        ----------
        data : LimitOffset
            Data required to apply a `LIMIT ... OFFSET ...` clause to the query.
        """
        self.select = self.select.limit(data.limit).offset(data.offset)

    def filter_on_datetime_field(self, data: BeforeAfter) -> None:
        """
        Add where-clause(s) to the query.

        Parameters
        ----------
        data : BeforeAfter
            Data required to apply a date/time based filter on the query.
        """
        field = getattr(self.model_type, data.field_name)
        if data.before is not None:
            self.select = self.select.where(field < data.before)
        if data.after is not None:
            self.select = self.select.where(field > data.before)

    def filter_in_collection(self, data: CollectionFilter) -> None:
        """
        Add a `...WHERE ... IN (...)` clause to the query.

        Parameters
        ----------
        data : CollectionFilter
            Required data for constructing the `IN` clause for the query.
        """
        if data.values is not None:
            self.select = self.select.where(
                getattr(self.model_type, data.field_name).in_(data.values)
            )

    async def scalars(self, **kwargs: Any) -> ScalarResult[T_model]:
        """
        Executes the repository select query, and returns response from
        [`AsyncResult.scalars()`][sqlalchemy.ext.asyncio.AsyncResult.scalars].

        Parameters
        ----------
        **kwargs : Any
            Passed as kwargs to [`execute()`][starlite_lib.repository.Base.execute].

        Returns
        -------
        ScalarResult
            Iterable of `T_model` instances.
        """
        with self.catch_sqlalchemy_exception():
            result = await self.execute(self.select, **kwargs)
            # noinspection PyUnresolvedReferences
            return result.scalars()

    def check_not_found(self, instance_or_none: T | None) -> T:
        """
        Responsible for raising the [`Base.not_found_error_type`][starlite_lib.repository.Base.not_found_error_type]
        on access of a [`scalar()`][starlite_lib.repository.Base.scalar] query result where no
        result is found.

        Parameters
        ----------
        instance_or_none : T | None
            Response from SQLAlchemy's [`scalar_one_or_none()`][sqlalchemy.ext.asyncio.AsyncResult.scalar_one_or_none]
            or similar.

        Returns
        -------
        T
            The scalar response instance, guaranteed not `None`.

        Raises
        ------
        Base.not_found_error_type
            If `instance_or_none` is `None`.
        """
        if instance_or_none is None:
            raise self.not_found_error_type
        return instance_or_none

    async def scalar(self, **kwargs: Any) -> T_model:
        """
        Get a scalar result from `self.select`.

        If `self.select` returns more than a single result, a `RepositoryException` is raised.

        Parameters
        ----------
        **kwargs : Any
            Passed through to `execute()`.

        Returns
        -------
        T_model
            The type returned by `self.select`

        Raises
        ------
        NotFoundException
            If `self.select` returns no rows.

        RepositoryException
            If `self.select` returns more than a single row.
        """
        with self.catch_sqlalchemy_exception():
            result = await self.execute(self.select, **kwargs)
            # this will raise for multiple results if the select hasn't been filtered to only return
            # a single result by this point.
            # noinspection PyUnresolvedReferences
            return self.check_not_found(result.scalar_one_or_none())

    # update

    @staticmethod
    def update_model(model: T, data: abc.Mapping[str, Any]) -> T:
        """
        Simple helper for setting key/values from `data` as attributes on `model`.

        Parameters
        ----------
        model : T
            Model instance to be updated.
        data : Mapping[str, Any]
            Mapping of data to set as key/value pairs on `model`.

        Returns
        -------
        T
            Key/value pairs from `data` have been set on the model.
        """
        for k, v in data.items():
            setattr(model, k, v)
        return model

    async def update(self, data: abc.Mapping[str, Any]) -> T_model:
        """
        Update the model returned from `self.select` with key/val pairs from `data`.

        Parameters
        ----------
        data : Mapping[str, Any]
            Key/value pairs used to set attribute vals on result of `self.select`.

        Returns
        -------
        T_model
            The type returned by `self.select`

        Raises
        ------
        Base.not_found_error_type
            If `self.select` returns no rows.
        Base.base_error_type
            If `self.select` returns more than a single row.
        """
        model = await self.scalar()
        return await self.add_flush_refresh(self.update_model(model, data))

    async def upsert(self, data: dict[str, Any]) -> T_model:
        """
        Update the model returned from `self.select` but if the instance doesn't exist create
        it and populate from ``data``.

        Parameters
        ----------
        data : Mapping[str, Any]
            Key/value pairs used to set attribute vals on result of `self.select`, or new instance
            of `self.model`.

        Returns
        -------
        T_model
            The type returned by `self.select`

        Raises
        ------
        Base.base_error_type
            If `self.select` returns more than a single row.
        """
        try:
            model = await self.scalar()
        except self.not_found_error_type:
            model = await self.create(data)
        else:
            self.update_model(model, data)
            await self.add_flush_refresh(model)
        return model

    # delete

    async def delete(self) -> T_model:
        """
        Delete and return the instance returned from `self.scalar()`.

        Returns
        -------
        T_model
            The type returned by `self.select`

        Raises
        ------
        Base.not_found_error_type
            If `self.select` returns no rows.
        Base.base_error_type
            If `self.select` returns more than a single row.
        """
        with self.catch_sqlalchemy_exception():
            instance = await self.scalar()
            await self.session.delete(instance)
            await self.session.flush()
            return instance
