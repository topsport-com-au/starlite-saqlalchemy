from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
from starlite import Starlite
from starlite.testing import TestClient
from starlite_saqlalchemy import ConfigureApp

if TYPE_CHECKING:
    from collections import abc


@pytest.fixture()
def app() -> Starlite:
    """Always use this `app` fixture and never do `from app.main import app`
    inside a test module. We need to delay import of the `app.main` module
    until as late as possible to ensure we can mock everything necessary before
    the application instance is constructed.

    Returns:
        The application instance.
    """
    return Starlite(route_handlers=[], on_app_init=[ConfigureApp()])


@pytest.fixture()
def client(app: "Starlite") -> "abc.Iterator[TestClient]":  # pylint: disable=redefined-outer-name
    """Client instance attached to app.

    Args:
        app: The app for testing.

    Returns:
        Test client instance.
    """
    with TestClient(app=app) as c:
        yield c


@pytest.fixture()
def raw_authors() -> list[dict[str, Any]]:
    """

    Returns:
        Raw set of author data that can either be inserted into tables for integration tests, or
        used to create `Author` instances for unit tests.
    """
    return [
        {
            "id": UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"),
            "name": "Agatha Christie",
            "dob": date(1890, 9, 15),
            "created": datetime.min,
            "updated": datetime.min,
        },
        {
            "id": UUID("5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"),
            "name": "Leo Tolstoy",
            "dob": date(1828, 9, 9),
            "created": datetime.min,
            "updated": datetime.min,
        },
    ]
