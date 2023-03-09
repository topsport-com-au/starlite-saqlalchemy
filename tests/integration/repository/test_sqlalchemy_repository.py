from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from starlite_saqlalchemy.exceptions import StarliteSaqlalchemyError
from tests.utils.domain import authors


@pytest.fixture(name="session")
def fx_session(engine: AsyncEngine) -> AsyncSession:
    return async_sessionmaker(bind=engine)()


@pytest.fixture(name="repo")
def fx_repo(session: AsyncSession) -> authors.Repository:
    return authors.Repository(session=session)


def test_filter_by_kwargs_with_incorrect_attribute_name(repo: authors.Repository) -> None:
    """Test SQLALchemy filter by kwargs with invalid column name.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    with pytest.raises(StarliteSaqlalchemyError):
        repo.filter_collection_by_kwargs(repo.statement, whoops="silly me")


async def test_repo_count_method(repo: authors.Repository) -> None:
    """Test SQLALchemy count with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    assert await repo.count() == 2


async def test_repo_list_and_count_method(
    raw_authors: list[dict[str, Any]],
    repo: authors.Repository,
) -> None:
    """Test SQLALchemy list with count in sqlite.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        repo (AuthorRepository): The author mock repository
    """
    exp_count = len(raw_authors)
    collection, count = await repo.list_and_count()
    assert exp_count == count
    assert isinstance(collection, list)
    assert len(collection) == exp_count


async def test_repo_list_method(
    raw_authors: list[dict[str, Any]],
    repo: authors.Repository,
) -> None:
    """Test SQLALchemy list with sqlite.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        repo (AuthorRepository): The author mock repository
    """
    exp_count = len(raw_authors)
    collection = await repo.list()
    assert isinstance(collection, list)
    assert len(collection) == exp_count


async def test_repo_add_method(
    raw_authors: list[dict[str, Any]],
    repo: authors.Repository,
) -> None:
    """Test SQLALchemy Add with sqlite.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        repo (AuthorRepository): The author mock repository
    """
    exp_count = len(raw_authors) + 1
    new_author = authors.Author(name="Testing", dob=datetime.now())
    obj = await repo.add(new_author)
    count = await repo.count()
    assert exp_count == count
    assert isinstance(obj, authors.Author)
    assert new_author.name == obj.name
    assert obj.id is not None


async def test_repo_add_many_method(
    raw_authors: list[dict[str, Any]],
    repo: authors.Repository,
) -> None:
    """Test SQLALchemy Add Many with sqlite.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        repo (AuthorRepository): The author mock repository
    """
    exp_count = len(raw_authors) + 2
    objs = await repo.add_many(
        [
            authors.Author(name="Testing 2", dob=datetime.now()),
            authors.Author(name="Cody", dob=datetime.now()),
        ],
    )
    count = await repo.count()
    assert exp_count == count
    assert isinstance(objs, list)
    assert len(objs) == 2
    for obj in objs:
        assert obj.id is not None
        assert obj.name in {"Testing 2", "Cody"}


async def test_repo_update_many_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Update Many with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    objs = await repo.list()
    for idx, obj in enumerate(objs):
        obj.name = f"Update {idx}"
    objs = await repo.update_many(objs)
    for obj in objs:
        assert obj.name.startswith("Update")


async def test_repo_update_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Update with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    obj = await repo.get(UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"))
    obj.name = "Updated Name"
    updated_obj = await repo.update(obj)
    assert updated_obj.name == obj.name


async def test_repo_delete_method(repo: authors.Repository) -> None:
    """Test SQLALchemy delete with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    obj = await repo.delete(UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"))
    assert obj.id == UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b")


async def test_repo_delete_many_method(repo: authors.Repository) -> None:
    """Test SQLALchemy delete many with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    all_objs = await repo.list()
    ids_to_delete = [existing_obj.id for existing_obj in all_objs]
    objs = await repo.delete_many(ids_to_delete)
    assert len(objs) > 0
    count = await repo.count()
    assert count == 0


async def test_repo_get_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Get with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    obj = await repo.get(UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"))
    assert obj.name == "Agatha Christie"


async def test_repo_get_one_or_none_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Get One with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    obj = await repo.get_one_or_none(id=UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"))
    assert obj is not None
    assert obj.name == "Agatha Christie"
    none_obj = await repo.get_one_or_none(name="I don't exist")
    assert none_obj is None


async def test_repo_get_one_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Get One with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    obj = await repo.get_one(id=UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"))
    assert obj is not None
    assert obj.name == "Agatha Christie"
    with pytest.raises(StarliteSaqlalchemyError):
        _ = await repo.get_one(name="I don't exist")


async def test_repo_get_or_create_method(repo: authors.Repository) -> None:
    """Test SQLALchemy Get or create with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    existing_obj, existing_created = await repo.get_or_create(name="Agatha Christie")
    assert existing_obj.id == UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert existing_created is False
    new_obj, new_created = await repo.get_or_create(name="New Author")
    assert new_obj.id is not None
    assert new_obj.name == "New Author"
    assert new_created


async def test_repo_upsert_method(repo: authors.Repository) -> None:
    """Test SQLALchemy upsert with sqlite.

    Args:
        repo (AuthorRepository): The author mock repository
    """
    existing_obj = await repo.get_one(name="Agatha Christie")
    existing_obj.name = "Agatha C."
    upsert_update_obj = await repo.upsert(existing_obj)
    assert upsert_update_obj.id == UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert upsert_update_obj.name == "Agatha C."

    upsert_insert_obj = await repo.upsert(authors.Author(name="An Author"))
    assert upsert_insert_obj.id is not None
    assert upsert_insert_obj.name == "An Author"

    # ensures that it still works even if the ID is added before insert
    upsert2_insert_obj = await repo.upsert(authors.Author(id=uuid4(), name="Another Author"))
    assert upsert2_insert_obj.id is not None
    assert upsert2_insert_obj.name == "Another Author"
