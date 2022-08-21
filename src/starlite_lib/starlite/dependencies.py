from dataclasses import dataclass
from typing import Any

from starlite import Dependency

from starlite_lib.repository import BeforeAfter, CollectionFilter, LimitOffset


@dataclass
class Filters:
    id: CollectionFilter | None
    """Filter for scoping query to limited set of identities."""
    created: BeforeAfter | None
    """Filter for scoping query to instance creation date/time."""
    updated: BeforeAfter | None
    """Filter for scoping query to instance update date/time."""
    limit_offset: LimitOffset | None
    """Filter for query pagination."""

    def to_dict(self) -> dict[str, Any]:
        """
        Dict that maps the parameter name used in the `filters()` dependency function to the
        filter dataclass.

        Returns
        -------
        dict[str, Any]
            Supports unpacking into `filters()`
        """
        return {
            "id_filter": self.id,
            "created_filter": self.created,
            "updated_filter": self.updated,
            "limit_offset": self.limit_offset,
        }


def filters(
    id_filter: CollectionFilter | None = Dependency(),
    created_filter: BeforeAfter | None = Dependency(),
    updated_filter: BeforeAfter | None = Dependency(),
    limit_offset: LimitOffset | None = Dependency(),
) -> Filters:
    """
    Common collection route filtering dependencies.

    Add all filters to any route by including this function as a dependency, e.g:

        @get_collection
        def get_collection_handler(filters: Filters) -> ...:
            ...

    The dependency is provided at the application layer, so only need to inject the dependency where
    necessary.

    Parameters
    ----------
    id_filter : repository.CollectionFilter
        Filter for scoping query to limited set of identities.
    created_filter : repository.BeforeAfter
        Filter for scoping query to instance creation date/time.
    updated_filter : repository.BeforeAfter
        Filter for scoping query to instance update date/time.
    limit_offset : repository.LimitOffset
        Filter for query pagination.

    Returns
    -------
    Filters
        Datastructure that aggregates collection query filters.
    """
    return Filters(
        id=id_filter,
        created=created_filter,
        updated=updated_filter,
        limit_offset=limit_offset,
    )
