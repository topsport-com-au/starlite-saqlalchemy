import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from starlite_saqlalchemy.repository.exceptions import RepositoryException
from tests.utils.domain import authors


@pytest.fixture(name="session")
def fx_session(engine: AsyncEngine) -> AsyncSession:
    return async_sessionmaker(bind=engine)()


@pytest.fixture(name="repo")
def fx_repo(session: AsyncSession) -> authors.Repository:
    return authors.Repository(session=session)


def test_filter_by_kwargs_with_incorrect_attribute_name(repo: authors.Repository) -> None:
    with pytest.raises(RepositoryException):
        repo.filter_collection_by_kwargs(whoops="silly me")
