"""Unit test specific config."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from saq.job import Job
from starlite.datastructures import State
from starlite.enums import ScopeType
from starlite.testing import TestClient

from starlite_saqlalchemy import sqlalchemy_plugin, worker
from starlite_saqlalchemy.testing import GenericMockRepository
from tests.utils.domain.authors import Author
from tests.utils.domain.authors import Service as AuthorService
from tests.utils.domain.books import Book
from tests.utils.domain.books import Service as BookService

from ..utils import controllers

if TYPE_CHECKING:
    from collections import abc

    from starlite import Starlite
    from starlite.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope


@pytest.fixture(scope="session", autouse=True)
def _patch_sqlalchemy_plugin() -> abc.Iterator:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        sqlalchemy_plugin.SQLAlchemyConfig,  # type:ignore[attr-defined]
        "on_shutdown",
        MagicMock(),
    )
    yield
    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def _patch_worker() -> abc.Iterator:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(worker.Worker, "on_app_startup", MagicMock())
    monkeypatch.setattr(worker.Worker, "stop", MagicMock())
    yield
    monkeypatch.undo()


@pytest.fixture(autouse=True)
def _clear_mock_repo_collections() -> None:
    """Ensure all tests start with fresh collections."""
    # pylint: disable=protected-access
    GenericMockRepository._collections = {}  # type:ignore[misc]


@pytest.fixture(name="author_repository_type")
def fx_author_repository_type(
    authors: list[Author], monkeypatch: pytest.MonkeyPatch
) -> type[GenericMockRepository[Author]]:
    """Mock Author repository, pre-seeded with collection data."""

    class AuthorRepository(GenericMockRepository[Author]):
        """Mock Author repo."""

        model_type = Author

    AuthorRepository.seed_collection(authors)
    monkeypatch.setattr(AuthorService, "repository_type", AuthorRepository)
    return AuthorRepository


@pytest.fixture(name="author_repository")
def fx_author_repository(
    author_repository_type: type[GenericMockRepository[Author]],
) -> GenericMockRepository[Author]:
    """Mock Author repository instance."""
    return author_repository_type()


@pytest.fixture(name="book_repository_type")
def fx_book_repository_type(
    books: list[Book], monkeypatch: pytest.MonkeyPatch
) -> type[GenericMockRepository[Book]]:
    """Mock Book repository, pre-seeded with collection data."""

    class BookRepository(GenericMockRepository[Book]):
        """Mock book repo."""

        model_type = Book

    BookRepository.seed_collection(books)
    monkeypatch.setattr(BookService, "repository_type", BookRepository)
    return BookRepository


@pytest.fixture(name="book_repository")
def fx_book_repository(
    book_repository_type: type[GenericMockRepository[Book]],
) -> GenericMockRepository[Book]:
    """Mock Book repo instance."""
    return book_repository_type()


@pytest.fixture(name="client")
def fx_client(app: Starlite) -> abc.Iterator[TestClient]:
    """Client instance attached to app.

    Args:
        app: The app for testing.

    Returns:
        Test client instance.
    """
    with TestClient(app=app) as client_:
        yield client_


@pytest.fixture()
def http_response_start() -> HTTPResponseStartEvent:
    """ASGI message for start of response."""
    return {"type": "http.response.start", "status": 200, "headers": []}


@pytest.fixture()
def http_response_body() -> HTTPResponseBodyEvent:
    """ASGI message for interim, and final response body messages.

    Note:
        `more_body` is `True` for interim body messages.
    """
    return {"type": "http.response.body", "body": b"body", "more_body": False}


@pytest.fixture()
def http_scope(app: Starlite) -> HTTPScope:
    """Minimal ASGI HTTP connection scope."""
    return {
        "headers": [],
        "app": app,
        "asgi": {"spec_version": "whatever", "version": "3.0"},
        "auth": None,
        "client": None,
        "extensions": None,
        "http_version": "3",
        "path": "/wherever",
        "path_params": {},
        "query_string": b"",
        "raw_path": b"/wherever",
        "root_path": "/",
        "route_handler": controllers.get_author,
        "scheme": "http",
        "server": None,
        "session": {},
        "state": {},
        "user": None,
        "method": "GET",
        "type": ScopeType.HTTP,
    }


@pytest.fixture()
def state() -> State:
    """Starlite application state datastructure."""
    return State()


@pytest.fixture()
def job() -> Job:
    """SAQ Job instance."""
    return Job(function="whatever", kwargs={"a": "b"})
