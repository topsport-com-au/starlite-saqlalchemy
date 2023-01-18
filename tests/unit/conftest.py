"""Unit test specific config."""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlite.datastructures import State
from starlite.enums import ScopeType

from starlite_saqlalchemy import constants

if constants.IS_SAQ_INSTALLED:
    from saq.job import Job

if TYPE_CHECKING:

    from starlite import Starlite
    from starlite.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope

    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.authors import Author
    from tests.utils.domain.books import Book


@pytest.fixture(name="author_repository_type", autouse=constants.IS_SQLALCHEMY_INSTALLED)
def fx_author_repository_type(
    authors: list[Author], monkeypatch: pytest.MonkeyPatch
) -> type[GenericMockRepository[Author]]:
    """Mock Author repository, pre-seeded with collection data."""
    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.authors import Author
    from tests.utils.domain.authors import Service as AuthorService

    repo = GenericMockRepository[Author]
    repo.seed_collection(authors)
    monkeypatch.setattr(AuthorService, "repository_type", repo)
    return repo


@pytest.fixture(name="author_repository", autouse=constants.IS_SQLALCHEMY_INSTALLED)
def fx_author_repository(
    author_repository_type: type[GenericMockRepository[Author]],
) -> GenericMockRepository[Author]:
    """Mock Author repository instance."""
    return author_repository_type()


@pytest.fixture(name="book_repository_type", autouse=constants.IS_SQLALCHEMY_INSTALLED)
def fx_book_repository_type(
    books: list[Book], monkeypatch: pytest.MonkeyPatch
) -> type[GenericMockRepository[Book]]:
    """Mock Book repository, pre-seeded with collection data."""
    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.books import Book
    from tests.utils.domain.books import Service as BookService

    class BookRepository(GenericMockRepository[Book]):
        """Mock book repo."""

        model_type = Book

    BookRepository.seed_collection(books)
    monkeypatch.setattr(BookService, "repository_type", BookRepository)
    return BookRepository


@pytest.fixture(name="book_repository", autouse=constants.IS_SQLALCHEMY_INSTALLED)
def fx_book_repository(
    book_repository_type: type[GenericMockRepository[Book]],
) -> GenericMockRepository[Book]:
    """Mock Book repo instance."""
    return book_repository_type()


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
    from ..utils import controllers

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


@pytest.fixture(autouse=constants.IS_SAQ_INSTALLED)
def job() -> Job:
    """SAQ Job instance."""
    return Job(function="whatever", kwargs={"a": "b"})


@pytest.fixture()
def state() -> State:
    """Starlite application state datastructure."""
    return State()
