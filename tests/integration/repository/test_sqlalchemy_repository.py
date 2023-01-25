from __future__ import annotations

from typing import Any

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
    select_ = repo._create_select_for_model()
    with pytest.raises(StarliteSaqlalchemyError):
        repo.filter_collection_by_kwargs(select_, whoops="silly me")


async def test_repo_count_method(repo: authors.Repository) -> None:
    assert await repo.count() == 2


async def test_repo_list_and_count_method(
    raw_authors: list[dict[str, Any]], repo: authors.Repository
) -> None:
    exp_count = len(raw_authors)
    collection, count = await repo.list_and_count()
    assert exp_count == count
    assert isinstance(collection, list)
    assert len(collection) == exp_count
