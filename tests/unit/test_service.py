"""Tests for Service object patterns."""
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import orjson

from starlite_saqlalchemy import service, sqlalchemy_plugin, worker
from tests.utils import domain

if TYPE_CHECKING:
    from pytest import MonkeyPatch


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
