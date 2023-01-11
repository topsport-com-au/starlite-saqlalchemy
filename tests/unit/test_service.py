"""Tests for Service object patterns."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from starlite_saqlalchemy import db, service, worker
from starlite_saqlalchemy.exceptions import NotFoundError
from tests.utils import domain

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from starlite_saqlalchemy.testing import GenericMockRepository


@pytest.fixture(autouse=True)
def _patch_author_service(
    author_repository_type: GenericMockRepository,  # pylint: disable=unused-argument
) -> None:
    """Patch the repository for all tests."""


async def test_service_create() -> None:
    """Test repository create action."""
    resp = await domain.authors.Service().create(
        domain.authors.Author(name="someone", dob=date.min)
    )
    assert resp.name == "someone"
    assert resp.dob == date.min


async def test_service_list() -> None:
    """Test repository list action."""
    resp = await domain.authors.Service().list()
    assert len(resp) == 2


async def test_service_update() -> None:
    """Test repository update action."""
    service_obj = domain.authors.Service()
    author, _ = await service_obj.list()
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.update(author.id, author)
    assert resp.name == "different"


async def test_service_upsert_update() -> None:
    """Test repository upsert action for update."""
    service_obj = domain.authors.Service()
    author, _ = await service_obj.list()
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "different"


async def test_service_upsert_create() -> None:
    """Test repository upsert action for create."""
    author = domain.authors.Author(id=uuid4(), name="New Author")
    resp = await domain.authors.Service().upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "New Author"


async def test_service_get() -> None:
    """Test repository get action."""
    service_obj = domain.authors.Service()
    author, _ = await service_obj.list()
    retrieved = await service_obj.get(author.id)
    assert author is retrieved


async def test_service_delete() -> None:
    """Test repository delete action."""
    service_obj = domain.authors.Service()
    author, _ = await service_obj.list()
    deleted = await service_obj.delete(author.id)
    assert author is deleted


async def test_make_service_callback(
    raw_authors: list[dict[str, Any]], monkeypatch: "MonkeyPatch"
) -> None:
    """Tests loading and retrieval of service object types."""
    recv_cb_mock = AsyncMock()
    monkeypatch.setattr(service.Service, "receive_callback", recv_cb_mock, raising=False)
    await service.make_service_callback(
        {},
        service_type_id="tests.utils.domain.authors.Service",
        service_method_name="receive_callback",
        raw_obj=raw_authors[0],
    )
    recv_cb_mock.assert_called_once_with(raw_obj=raw_authors[0])


async def test_make_service_callback_raises_runtime_error(
    raw_authors: list[dict[str, Any]]
) -> None:
    """Tests loading and retrieval of service object types."""
    with pytest.raises(KeyError):
        await service.make_service_callback(
            {},
            service_type_id="tests.utils.domain.LSKDFJ",
            service_method_name="receive_callback",
            raw_obj=raw_authors[0],
        )


async def test_enqueue_service_callback(monkeypatch: "MonkeyPatch") -> None:
    """Tests that job enqueued with desired arguments."""
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker.queue, "enqueue", enqueue_mock)
    service_instance = domain.authors.Service(session=db.async_session_factory())
    await service_instance.enqueue_background_task("receive_callback", raw_obj={"a": "b"})
    enqueue_mock.assert_called_once_with(
        "make_service_callback",
        service_type_id="tests.utils.domain.authors.Service",
        service_method_name="receive_callback",
        raw_obj={"a": "b"},
    )


async def test_service_new_context_manager() -> None:
    """Simple test of `Service.new()` context manager behavior."""
    async with service.Service[domain.authors.Author].new() as service_obj:
        assert isinstance(service_obj, service.Service)


async def test_service_method_default_behavior() -> None:
    """Test default behavior of base service methods."""
    service_obj = service.Service[object]()
    data = object()
    assert await service_obj.create(data) is data
    assert await service_obj.list() == []
    assert await service_obj.update("abc", data) is data
    assert await service_obj.upsert("abc", data) is data
    with pytest.raises(NotFoundError):
        await service_obj.get("abc")
    with pytest.raises(NotFoundError):
        await service_obj.delete("abc")
