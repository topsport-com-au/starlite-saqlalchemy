# pylint: disable=wrong-import-position,wrong-import-order
from __future__ import annotations

import pytest

from starlite_saqlalchemy.db import orm
from starlite_saqlalchemy.exceptions import ConflictError, StarliteSaqlalchemyError
from starlite_saqlalchemy.testing.generic_mock_repository import GenericMockRepository
from tests.utils.domain.authors import Author
from tests.utils.domain.books import Book


async def test_repo_raises_conflict_if_add_with_id(
    authors: list[Author],
    author_repository: GenericMockRepository[Author],
) -> None:
    """Test mock repo raises conflict if add identified entity."""
    with pytest.raises(ConflictError):
        await author_repository.add(authors[0])


def test_generic_mock_repository_parametrization() -> None:
    """Test that the mock repository handles multiple types."""
    author_repo = GenericMockRepository[Author]
    book_repo = GenericMockRepository[Book]
    assert author_repo.model_type is Author  # type:ignore[misc]
    assert book_repo.model_type is Book  # type:ignore[misc]


def test_generic_mock_repository_seed_collection(
    author_repository_type: type[GenericMockRepository[Author]],
) -> None:
    """Test seeding instances."""
    author_repository_type.seed_collection([Author(id="abc")])
    assert "abc" in author_repository_type.collection


def test_generic_mock_repository_clear_collection(
    author_repository_type: type[GenericMockRepository[Author]],
) -> None:
    """Test clearing collection for type."""
    author_repository_type.clear_collection()
    assert not author_repository_type.collection


def test_generic_mock_repository_filter_collection_by_kwargs(
    author_repository: GenericMockRepository[Author],
) -> None:
    """Test filtering the repository collection by kwargs."""
    author_repository.filter_collection_by_kwargs(name="Leo Tolstoy")
    assert len(author_repository.collection) == 1
    assert list(author_repository.collection.values())[0].name == "Leo Tolstoy"


def test_generic_mock_repository_filter_collection_by_kwargs_and_semantics(
    author_repository: GenericMockRepository[Author],
) -> None:
    """Test that filtering by kwargs has `AND` semantics when multiple kwargs,
    not `OR`."""
    author_repository.filter_collection_by_kwargs(name="Agatha Christie", dob="1828-09-09")
    assert len(author_repository.collection) == 0


def test_generic_mock_repository_raises_repository_exception_if_named_attribute_doesnt_exist(
    author_repository: GenericMockRepository[Author],
) -> None:
    """Test that a repo exception is raised if a named attribute doesn't
    exist."""
    with pytest.raises(StarliteSaqlalchemyError):
        author_repository.filter_collection_by_kwargs(cricket="ball")


async def test_sets_created_updated_on_add() -> None:
    """Test that the repository updates the 'created' and 'updated' timestamps
    if necessary."""

    class Model(orm.AuditBase):
        """Inheriting from AuditBase gives the model 'created' and 'updated'
        columns."""

        ...

    instance = Model()
    assert "created" not in vars(instance)
    assert "updated" not in vars(instance)

    instance = await GenericMockRepository[Model]().add(instance)
    assert "created" in vars(instance)
    assert "updated" in vars(instance)


async def test_sets_updated_on_update(author_repository: GenericMockRepository[Author]) -> None:
    """Test that the repository updates the 'updated' timestamp if
    necessary."""

    instance = list(author_repository.collection.values())[0]
    original_updated = instance.updated
    instance = await author_repository.update(instance)
    assert instance.updated > original_updated


async def test_does_not_set_created_updated() -> None:
    """Test that the repository does not update the 'updated' timestamps when
    appropriate."""

    class Model(orm.Base):
        """Inheriting from Base means the model has no created/updated
        timestamp columns."""

        ...

    instance = Model()
    repo = GenericMockRepository[Model]()
    assert "created" not in vars(instance)
    assert "updated" not in vars(instance)
    instance = await repo.add(instance)
    assert "created" not in vars(instance)
    assert "updated" not in vars(instance)
    instance = await repo.update(instance)
    assert "created" not in vars(instance)
    assert "updated" not in vars(instance)
