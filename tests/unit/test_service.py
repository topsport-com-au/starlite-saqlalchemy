"""Tests for Service object patterns."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock
from uuid import uuid4

import orjson
import pytest

from starlite_saqlalchemy import service, sqlalchemy_plugin, worker
from tests.utils import domain

if TYPE_CHECKING:
    from pytest import MonkeyPatch


ServiceType = service.Service[domain.Author]


@pytest.fixture(name="service_obj")
def fx_service() -> ServiceType:
    """Service object backed by mock repository."""

    class Service(service.Service[domain.Author]):
        repository_type = domain.Repository

    return Service()


async def test_service_create(service_obj: ServiceType) -> None:
    """Test repository create action."""
    resp = await service_obj.create(domain.Author(name="someone", dob=date.min))
    assert resp.name == "someone"
    assert resp.dob == date.min


async def test_service_list(service_obj: ServiceType) -> None:
    """Test repository list action."""
    resp = await service_obj.list()
    assert len(resp) == 2


async def test_service_update(service_obj: ServiceType) -> None:
    """Test repository update action."""
    author, _ = await service_obj.list()
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.update(author.id, author)
    assert resp.name == "different"


async def test_service_upsert_update(service_obj: ServiceType) -> None:
    """Test repository upsert action for update."""
    author, _ = await service_obj.list()
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "different"


async def test_service_upsert_create(service_obj: ServiceType) -> None:
    """Test repository upsert action for create."""
    author = domain.Author(id=uuid4(), name="New Author")
    resp = await service_obj.upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "New Author"


async def test_service_get(service_obj: ServiceType) -> None:
    """Test repository get action."""
    author, _ = await service_obj.list()
    retrieved = await service_obj.get(author.id)
    assert author is retrieved


async def test_service_delete(service_obj: ServiceType) -> None:
    """Test repository delete action."""
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
        service_module_name="tests.utils.domain",
        service_type_fqdn="Service",
        service_method_name="receive_callback",
        raw_obj=orjson.loads(orjson.dumps(raw_authors[0], default=str)),
    )
    recv_cb_mock.assert_called_once_with(
        raw_obj={
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "name": "Agatha Christie",
            "dob": "1890-09-15",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
    )


async def test_make_service_callback_raises_runtime_error(
    raw_authors: list[dict[str, Any]], monkeypatch: "MonkeyPatch"
) -> None:
    """Tests loading and retrieval of service object types."""
    with pytest.raises(RuntimeError):
        await service.make_service_callback(
            {},
            service_module_name="tests.utils.domain",
            service_type_fqdn="Author.name",
            service_method_name="receive_callback",
            raw_obj=orjson.loads(orjson.dumps(raw_authors[0], default=str)),
        )


async def test_enqueue_service_callback(monkeypatch: "MonkeyPatch") -> None:
    """Tests that job enqueued with desired arguments."""
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker.queue, "enqueue", enqueue_mock)
    service_instance = domain.Service(session=sqlalchemy_plugin.async_session_factory())
    await service_instance.enqueue_background_task("receive_callback", raw_obj={"a": "b"})
    enqueue_mock.assert_called_once_with(
        "make_service_callback",
        service_module_name="tests.utils.domain",
        service_type_fqdn="Service",
        service_method_name="receive_callback",
        raw_obj={"a": "b"},
    )
