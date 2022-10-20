# pylint: disable=protected-access,redefined-outer-name
from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from starlite_saqlalchemy.repository.exceptions import (
    RepositoryConflictException,
    RepositoryException,
)
from starlite_saqlalchemy.repository.filters import BeforeAfter, CollectionFilter, LimitOffset
from starlite_saqlalchemy.repository.sqlalchemy import (
    SQLAlchemyRepository,
    wrap_sqlalchemy_exception,
)

if TYPE_CHECKING:
    from pytest import MonkeyPatch


@pytest.fixture()
def mock_repo() -> SQLAlchemyRepository:
    """SQLAlchemy repository with a mock model type."""

    class Repo(SQLAlchemyRepository[MagicMock]):
        model_type = MagicMock()  # pyright:ignore[reportGeneralTypeIssues]

    return Repo(session=AsyncMock(spec=AsyncSession), select_=MagicMock())


def test_wrap_sqlalchemy_integrity_error() -> None:
    with (pytest.raises(RepositoryConflictException), wrap_sqlalchemy_exception()):
        raise IntegrityError(None, None, Exception())


def test_wrap_sqlalchemy_generic_error() -> None:
    with (pytest.raises(RepositoryException), wrap_sqlalchemy_exception()):
        raise SQLAlchemyError


async def test_sqlalchemy_repo_add(mock_repo: SQLAlchemyRepository) -> None:
    mock_instance = MagicMock()
    instance = await mock_repo.add(mock_instance)
    assert instance is mock_instance
    mock_repo._session.add.assert_called_once_with(mock_instance)
    mock_repo._session.flush.assert_called_once()
    mock_repo._session.refresh.assert_called_once_with(mock_instance)
    mock_repo._session.expunge.assert_called_once_with(mock_instance)
    mock_repo._session.commit.assert_not_called()


async def test_sqlalchemy_repo_delete(mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch") -> None:
    mock_instance = MagicMock()
    monkeypatch.setattr(mock_repo, "get", AsyncMock(return_value=mock_instance))
    instance = await mock_repo.delete("instance-id")
    assert instance is mock_instance
    mock_repo._session.delete.assert_called_once_with(mock_instance)
    mock_repo._session.flush.assert_called_once()
    mock_repo._session.expunge.assert_called_once_with(mock_instance)
    mock_repo._session.commit.assert_not_called()


async def test_sqlalchemy_repo_get_member(mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch") -> None:
    mock_instance = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_instance)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance = await mock_repo.get("instance-id")
    assert instance is mock_instance
    mock_repo._session.expunge.assert_called_once_with(mock_instance)
    mock_repo._session.commit.assert_not_called()


async def test_sqlalchemy_repo_list(mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch") -> None:
    mock_instances = [MagicMock(), MagicMock()]
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=mock_instances)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instances = await mock_repo.list()
    assert instances == mock_instances
    mock_repo._session.expunge.assert_has_calls(*mock_instances)
    mock_repo._session.commit.assert_not_called()


async def test_sqlalchemy_repo_list_with_pagination(
    mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch"
) -> None:
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo._select.limit.return_value = mock_repo._select
    mock_repo._select.offset.return_value = mock_repo._select
    await mock_repo.list(LimitOffset(2, 3))
    mock_repo._select.limit.assert_called_once_with(2)
    mock_repo._select.limit().offset.assert_called_once_with(3)  # type:ignore[call-arg]


async def test_sqlalchemy_repo_list_with_before_after_filter(
    mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch"
) -> None:
    field_name = "updated"
    # model has to support comparison with the datetimes
    getattr(mock_repo.model_type, field_name).__lt__ = lambda self, compare: "lt"
    getattr(mock_repo.model_type, field_name).__gt__ = lambda self, compare: "gt"
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo._select.where.return_value = mock_repo._select
    await mock_repo.list(BeforeAfter(field_name, datetime.max, datetime.min))
    assert mock_repo._select.where.call_count == 2
    assert mock_repo._select.where.has_calls([call("gt"), call("lt")])


async def test_sqlalchemy_repo_list_with_collection_filter(
    mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch"
) -> None:
    field_name = "id"
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo._select.where.return_value = mock_repo._select
    values = [1, 2, 3]
    await mock_repo.list(CollectionFilter(field_name, values))
    mock_repo._select.where.assert_called_once()
    getattr(mock_repo.model_type, field_name).in_.assert_called_once_with(values)


async def test_sqlalchemy_repo_update(mock_repo: SQLAlchemyRepository, monkeypatch: "MonkeyPatch") -> None:
    id_ = 3
    mock_instance = MagicMock()
    get_id_value_mock = MagicMock(return_value=id_)
    monkeypatch.setattr(mock_repo, "get_id_attribute_value", get_id_value_mock)
    get_mock = AsyncMock()
    monkeypatch.setattr(mock_repo, "get", get_mock)
    mock_repo._session.merge.return_value = mock_instance
    instance = await mock_repo.update(mock_instance)
    assert instance is mock_instance
    mock_repo._session.merge.assert_called_once_with(mock_instance)
    mock_repo._session.flush.assert_called_once()
    mock_repo._session.refresh.assert_called_once_with(mock_instance)
    mock_repo._session.expunge.assert_called_once_with(mock_instance)
    mock_repo._session.commit.assert_not_called()


async def test_sqlalchemy_repo_upsert(mock_repo: SQLAlchemyRepository) -> None:
    mock_instance = MagicMock()
    mock_repo._session.merge.return_value = mock_instance
    instance = await mock_repo.upsert(mock_instance)
    assert instance is mock_instance
    mock_repo._session.merge.assert_called_once_with(mock_instance)
    mock_repo._session.flush.assert_called_once()
    mock_repo._session.refresh.assert_called_once_with(mock_instance)
    mock_repo._session.expunge.assert_called_once_with(mock_instance)
    mock_repo._session.commit.assert_not_called()


async def test_attach_to_session_unexpected_strategy_raises_valueerror(mock_repo: SQLAlchemyRepository) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        await mock_repo._attach_to_session(MagicMock(), strategy="t-rex")  # type:ignore[arg-type]


async def test_execute(mock_repo: SQLAlchemyRepository) -> None:
    await mock_repo._execute()
    mock_repo._session.execute.assert_called_once_with(mock_repo._select)


def test_filter_in_collection_noop_if_collection_empty(mock_repo: SQLAlchemyRepository) -> None:
    mock_repo._filter_in_collection("id", [])
    mock_repo._select.where.assert_not_called()
