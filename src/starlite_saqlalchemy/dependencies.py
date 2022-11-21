"""Application dependency providers."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from starlite import Dependency, Parameter, Provide

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)
from starlite_saqlalchemy.repository.types import FilterTypes

if TYPE_CHECKING:

    from starlite import Request  # noqa: F401

DTorNone = datetime | None

CREATED_FILTER_DEPENDENCY_KEY = "created_filter"
FILTERS_DEPENDENCY_KEY = "filters"
ID_FILTER_DEPENDENCY_KEY = "id_filter"
LIMIT_OFFSET_DEPENDENCY_KEY = "limit_offset"
UPDATED_FILTER_DEPENDENCY_KEY = "updated_filter"


def provide_id_filter(
    ids: list[UUID] | None = Parameter(query="ids", default=None, required=False)
) -> CollectionFilter[UUID]:
    """
    Args:
        ids: Parsed out of query params.

    Returns:
        Type consumed by `AbstractRepository.filter_in_collection()`
    """
    return CollectionFilter(field_name="id", values=ids or [])


def provide_created_filter(
    before: DTorNone = Parameter(query="created-before", default=None, required=False),
    after: DTorNone = Parameter(query="created-after", default=None, required=False),
) -> BeforeAfter:
    """
    Args:
        before: Filter for records created before this date/time.
        after: Filter for records created after this date/time.

    Returns:
        Type consumed by `Repository.filter_on_datetime_field()`.
    """
    return BeforeAfter("created", before, after)


def provide_updated_filter(
    before: DTorNone = Parameter(query="updated-before", default=None, required=False),
    after: DTorNone = Parameter(query="updated-after", default=None, required=False),
) -> BeforeAfter:
    """
    Args:
        before: Filter for records updated before this date/time.
        after: Filter for records updated after this date/time.

    Returns:
        Type consumed by `Repository.filter_on_datetime_field()`.
    """
    return BeforeAfter("updated", before, after)


def provide_limit_offset_pagination(
    page: int = Parameter(ge=1, default=1, required=False),
    page_size: int = Parameter(
        query="page-size",
        ge=1,
        default=settings.api.DEFAULT_PAGINATION_LIMIT,
        required=False,
    ),
) -> LimitOffset:
    """
    Args:
        page: LIMIT to apply to select.
        page_size: OFFSET to apply to select.

    Returns:
        Type consumed by `Repository.apply_limit_offset_pagination()`.
    """
    return LimitOffset(page_size, page_size * (page - 1))


def provide_filter_dependencies(
    created_filter: BeforeAfter = Dependency(skip_validation=True),
    updated_filter: BeforeAfter = Dependency(skip_validation=True),
    id_filter: CollectionFilter[UUID] = Dependency(skip_validation=True),
    limit_offset: LimitOffset = Dependency(skip_validation=True),
) -> list[FilterTypes]:
    """Inject filtering dependencies.

    Add all filters to any route by including this function as a dependency, e.g:

    ```python
    @get
    def get_collection_handler(filters: Filters) -> ...:
        ...
    ```

    The dependency is provided at the application layer, so only need to inject the dependency where
    it is required.

    Args:
        id_filter: Filter for scoping query to limited set of identities.
        created_filter: Filter for scoping query to instance creation date/time.
        updated_filter: Filter for scoping query to instance update date/time.
        limit_offset: Filter for query pagination.

    Returns:
        List of filters parsed from connection.
    """
    return [
        created_filter,
        id_filter,
        limit_offset,
        updated_filter,
    ]


def create_collection_dependencies() -> dict[str, Provide]:
    """Build mapping of collection dependencies.

    Returns:
        A dictionary of provides for pagination endpoints.
    """
    return {
        LIMIT_OFFSET_DEPENDENCY_KEY: Provide(provide_limit_offset_pagination),
        UPDATED_FILTER_DEPENDENCY_KEY: Provide(provide_updated_filter),
        CREATED_FILTER_DEPENDENCY_KEY: Provide(provide_created_filter),
        ID_FILTER_DEPENDENCY_KEY: Provide(provide_id_filter),
        FILTERS_DEPENDENCY_KEY: Provide(provide_filter_dependencies),
    }
