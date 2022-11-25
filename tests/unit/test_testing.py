"""Test testing module."""

import pytest

from starlite_saqlalchemy import testing
from starlite_saqlalchemy.repository.exceptions import RepositoryConflictException
from tests.utils.domain.authors import Author
from tests.utils.domain.books import Book


async def test_repo_raises_conflict_if_add_with_id(
    authors: list[Author],
    author_repository: testing.GenericMockRepository[Author],
) -> None:
    """Test mock repo raises conflict if add identified entity."""
    with pytest.raises(RepositoryConflictException):
        await author_repository.add(authors[0])


def test_generic_mock_repository_parametrization() -> None:
    """Test that the mock repository handles multiple types."""
    # pylint: disable=pointless-statement,protected-access
    testing.GenericMockRepository[Author]
    testing.GenericMockRepository[Book]
    assert Author in testing.GenericMockRepository._collections  # type:ignore[misc]
    assert Book in testing.GenericMockRepository._collections  # type:ignore[misc]


def test_generic_mock_repository_seed_collection(
    author_repository_type: type[testing.GenericMockRepository[Author]],
) -> None:
    """Test seeding instances."""
    author_repository_type.seed_collection([Author(id="abc")])
    # pylint: disable=protected-access
    assert "abc" in author_repository_type._collections[Author]


def test_generic_mock_repository_clear_collection(
    author_repository_type: type[testing.GenericMockRepository[Author]],
) -> None:
    """Test clearing collection for type."""
    author_repository_type.clear_collection()
    # pylint: disable=protected-access
    assert not author_repository_type._collections[Author]
