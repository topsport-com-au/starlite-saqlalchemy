"""Tests for route generation functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlite import Provide, Starlite
from starlite.testing import TestClient

from starlite_saqlalchemy.dependencies import create_collection_dependencies
from starlite_saqlalchemy.router import create_collection_view
from tests.utils.domain.authors import ReadDTO, Service

if TYPE_CHECKING:
    from starlite_saqlalchemy.testing import GenericMockRepository


@pytest.fixture(autouse=True)
def _patch_author_service(
    author_repository_type: GenericMockRepository,  # pylint: disable=unused-argument
) -> None:
    """Patch the repository for all tests."""


@pytest.fixture(name="app")
def fx_app(
    author_repository_type: GenericMockRepository,  # pylint: disable=unused-argument
) -> Starlite:
    """Application instance with no registered handlers."""

    def provide_service() -> Service:
        """whoop."""
        return Service(db_session=None)

    dependencies = create_collection_dependencies()
    dependencies["service"] = Provide(provide_service)
    return Starlite(route_handlers=[], dependencies=dependencies, openapi_config=None)


def test_create_collection_view(app: Starlite) -> None:
    """Test collection route handler generation."""
    handler = create_collection_view(
        resource="authors", read_dto_type=ReadDTO, service_type=Service
    )
    app.register(handler)
    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.json() == [
        {
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
            "name": "Agatha Christie",
            "dob": "1890-09-15",
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
            "name": "Leo Tolstoy",
            "dob": "1828-09-09",
        },
    ]
