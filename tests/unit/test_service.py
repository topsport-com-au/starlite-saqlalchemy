"""Tests for Service object patterns."""
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock
from uuid import UUID

import orjson

from starlite_saqlalchemy import service, sqlalchemy_plugin, worker
from tests.utils import domain

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_internal_dto_cache() -> None:
    """Test ensures that the test domain has an entry in the dto cache for the
    Author model."""
    # pylint: disable=protected-access
    assert domain.Service in service.Service._INTERNAL_DTO_CACHE
    assert service.Service._INTERNAL_DTO_CACHE[domain.Service].__name__ == "__authorDTO"


async def test_make_service_callback(
    raw_authors: list[dict[str, Any]], monkeypatch: "MonkeyPatch"
) -> None:
    """Tests loading and retrieval of service object types."""
    recv_cb_mock = AsyncMock()
    monkeypatch.setattr(service.Service, "receive_callback", recv_cb_mock)
    await service.make_service_callback(
        {},
        service_module_name="tests.utils.domain",
        service_type_fqdn="Service",
        operation=service.Operation.UPDATE,
        raw_obj=orjson.loads(orjson.dumps(raw_authors[0], default=str)),
    )
    recv_cb_mock.assert_called_once_with(
        service.Operation.UPDATE,
        raw_obj={
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "name": "Agatha Christie",
            "dob": "1890-09-15",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
    )


async def test_enqueue_service_callback(
    raw_authors: list[dict[str, Any]], monkeypatch: "MonkeyPatch"
) -> None:
    """Tests that job enqueued with desired arguments."""
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker.queue, "enqueue", enqueue_mock)
    service_instance = domain.Service(sqlalchemy_plugin.async_session_factory())
    await service_instance.enqueue_callback(
        service.Operation.UPDATE, domain.Author(**raw_authors[0])
    )
    enqueue_mock.assert_called_once_with(
        "make_service_callback",
        service_module_name="tests.utils.domain",
        service_type_fqdn="Service",
        operation=service.Operation.UPDATE,
        raw_obj={
            "id": UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"),
            "created": datetime(1, 1, 1, 0, 0),
            "updated": datetime(1, 1, 1, 0, 0),
            "name": "Agatha Christie",
            "dob": date(1890, 9, 15),
        },
    )
