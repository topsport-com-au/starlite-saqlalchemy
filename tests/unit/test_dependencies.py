"""Dependency tests.

- tests datastructures produced by dependency provide functions
- tests injection of dependencies when declared in handler signatures
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from starlite import Starlite, get

from starlite_saqlalchemy import dependencies
from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)
from starlite_saqlalchemy.repository.types import FilterTypes  # noqa: TC002

if TYPE_CHECKING:
    from collections import abc

    from starlite.testing import TestClient


def test_id_filter() -> None:
    """Test datastructure produced by id filter dependency."""
    ids = [uuid4() for _ in range(3)]
    assert dependencies.provide_id_filter(ids) == CollectionFilter(field_name="id", values=ids)


@pytest.mark.parametrize(
    ("filter_", "field_name"),
    [
        (dependencies.provide_created_filter, "created"),
        (dependencies.provide_updated_filter, "updated"),
    ],
)
def test_before_after_filters(
    filter_: "abc.Callable[[datetime, datetime], BeforeAfter]", field_name: str
) -> None:
    """Test datastructure created by created/updated filters."""
    assert filter_(datetime.max, datetime.min) == BeforeAfter(
        field_name=field_name, before=datetime.max, after=datetime.min
    )


def test_limit_offset_pagination() -> None:
    """Test datastructure produced by limit offset pagination dependency."""
    assert dependencies.provide_limit_offset_pagination(10, 100) == LimitOffset(100, 900)


def test_provided_filters(app: "Starlite", client: "TestClient") -> None:
    """Tests collection route filters injected individually."""
    called = False
    path = f"/{uuid4()}"
    ids = [uuid4() for _ in range(2)]

    @get(path)
    def filtered_collection_route(
        created_filter: BeforeAfter,
        updated_filter: BeforeAfter,
        limit_offset: LimitOffset,
        id_filter: CollectionFilter,
    ) -> None:
        nonlocal called
        assert created_filter == BeforeAfter("created", datetime.max, datetime.min)
        assert updated_filter == BeforeAfter("updated", datetime.max, datetime.min)
        assert limit_offset == LimitOffset(2, 18)
        assert id_filter == CollectionFilter("id", ids)
        called = True

    app.register(filtered_collection_route)
    client.get(
        path,
        params={
            "created-before": str(datetime.max),
            "created-after": str(datetime.min),
            "updated-before": str(datetime.max),
            "updated-after": str(datetime.min),
            "page": 10,
            "page-size": 2,
            "ids": [str(id_) for id_ in ids],
        },
    )
    assert called


def test_filters_dependency(app: "Starlite", client: "TestClient") -> None:
    """Test collection route aggregate filters dependency."""
    called = False
    path = f"/{uuid4()}"
    ids = [uuid4() for _ in range(2)]

    @get(path)
    def filtered_collection_route(filters: list[FilterTypes]) -> None:
        nonlocal called
        assert filters == [
            BeforeAfter(field_name="created", before=datetime.max, after=datetime.min),
            CollectionFilter(field_name="id", values=ids),
            LimitOffset(limit=2, offset=18),
            BeforeAfter(field_name="updated", before=datetime.max, after=datetime.min),
        ]
        called = True

    app.register(filtered_collection_route)
    client.get(
        path,
        params={
            "created-before": str(datetime.max),
            "created-after": str(datetime.min),
            "updated-before": str(datetime.max),
            "updated-after": str(datetime.min),
            "page": 10,
            "page-size": 2,
            "ids": [str(id_) for id_ in ids],
        },
    )
    assert called
