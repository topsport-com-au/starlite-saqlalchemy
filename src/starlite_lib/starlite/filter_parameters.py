from datetime import datetime
from uuid import UUID

from starlite import Parameter

from starlite_lib.config import api_settings
from starlite_lib.repository import BeforeAfter, CollectionFilter, LimitOffset

DTorNone = datetime | None


def id_filter(
    ids: list[UUID] | None = Parameter(query="ids", default=None, required=False)
) -> CollectionFilter[UUID]:
    """
    Return type consumed by ``Repository.filter_in_collection()``.

    Parameters
    ----------
    ids : list[UUID] | None
        Parsed out of comma separated list of values in query params.

    Returns
    -------
    CollectionFilter[UUID]
    """
    return CollectionFilter(field_name="id", values=ids)


def created_filter(
    before: DTorNone = Parameter(query="created-before", default=None, required=False),
    after: DTorNone = Parameter(query="created-after", default=None, required=False),
) -> BeforeAfter:
    """
    Return type consumed by `Repository.filter_on_datetime_field()`.

    Parameters
    ----------
    before : datetime | None
        Filter for records updated before this date/time.
    after : datetime | None
        Filter for records updated after this date/time.
    """
    return BeforeAfter("created_date", before, after)


def updated_filter(
    before: DTorNone = Parameter(query="updated-before", default=None, required=False),
    after: DTorNone = Parameter(query="updated-after", default=None, required=False),
) -> BeforeAfter:
    """
    Return type consumed by `Repository.filter_on_datetime_field()`.
    Parameters
    ----------
    before : datetime | None
        Filter for records updated before this date/time.
    after : datetime | None
        Filter for records updated after this date/time.
    """
    return BeforeAfter("updated_date", before, after)


def limit_offset_pagination(
    page: int = Parameter(ge=1, default=1, required=False),
    page_size: int = Parameter(
        query="page-size",
        ge=1,
        default=api_settings.DEFAULT_PAGINATION_LIMIT,
        required=False,
    ),
) -> LimitOffset:
    """
    Return type consumed by `Repository.apply_limit_offset_pagination()`.
    Parameters
    ----------
    page : int
        LIMIT to apply to select.
    page_size : int
        OFFSET to apply to select.
    """
    return LimitOffset(page_size, page_size * (page - 1))
