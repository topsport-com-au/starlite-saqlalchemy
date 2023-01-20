from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from asyncpg.pgproto import pgproto

from starlite_saqlalchemy.constants import IS_SQLALCHEMY_INSTALLED

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch

    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.authors import Author
    from tests.utils.domain.books import Book

if not IS_SQLALCHEMY_INSTALLED:
    collect_ignore_glob = ["*"]


@pytest.fixture(autouse=True)
def _patch_bases(monkeypatch: MonkeyPatch) -> None:
    """Ensure new registry state for every test.

    This prevents errors such as "Table '...' is already defined for
    this MetaData instance...
    """
    from sqlalchemy.orm import DeclarativeBase

    from starlite_saqlalchemy.db import orm

    class NewBase(orm.CommonColumns, DeclarativeBase):
        ...

    class NewAuditBase(orm.AuditColumns, orm.CommonColumns, DeclarativeBase):
        ...

    monkeypatch.setattr(orm, "Base", NewBase)
    monkeypatch.setattr(orm, "AuditBase", NewAuditBase)


@pytest.fixture(name="authors")
def fx_authors(raw_authors: list[dict[str, Any]]) -> list[Author]:
    """Collection of parsed Author models."""
    from tests.utils.domain import authors

    mapped_authors = [authors.ReadDTO(**raw).to_mapped() for raw in raw_authors]
    # convert these to pgproto UUIDs as that is what we get back from sqlalchemy
    for author in mapped_authors:
        author.id = pgproto.UUID(str(author.id))
    return mapped_authors


@pytest.fixture(name="books")
def fx_books(raw_books: list[dict[str, Any]]) -> list[Book]:
    """Collection of parsed Book models."""
    from tests.utils.domain import books

    mapped_books = [books.ReadDTO(**raw).to_mapped() for raw in raw_books]
    # convert these to pgproto UUIDs as that is what we get back from sqlalchemy
    for book in mapped_books:
        book.id = pgproto.UUID(str(book.id))
    return mapped_books


@pytest.fixture(name="author_repository_type")
def fx_author_repository_type(
    authors: list[Author], monkeypatch: pytest.MonkeyPatch
) -> type[GenericMockRepository[Author]]:
    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.authors import Author, Service

    """Mock Author repository, pre-seeded with collection data."""
    repo = GenericMockRepository[Author]
    repo.seed_collection(authors)
    monkeypatch.setattr(Service, "repository_type", repo)
    return repo


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
    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )
    from tests.utils.domain.books import Book, Service

    class BookRepository(GenericMockRepository[Book]):
        """Mock book repo."""

        model_type = Book

    BookRepository.seed_collection(books)
    monkeypatch.setattr(Service, "repository_type", BookRepository)
    return BookRepository


@pytest.fixture(name="book_repository")
def fx_book_repository(
    book_repository_type: type[GenericMockRepository[Book]],
) -> GenericMockRepository[Book]:
    """Mock Book repo instance."""
    return book_repository_type()
