"""Tests for the SAQ async worker functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest
from asyncpg.pgproto import pgproto
from pydantic import BaseModel
from saq import Job

from starlite_saqlalchemy import service, worker

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_worker_decoder_handles_pgproto_uuid() -> None:
    """Test that the decoder can handle pgproto.UUID instances."""
    pg_uuid = pgproto.UUID("0448bde2-7c69-4e6b-9c03-7b217e3b563d")
    encoded = worker.encoder.encode(pg_uuid)
    assert encoded == b'"0448bde2-7c69-4e6b-9c03-7b217e3b563d"'


def test_worker_decoder_handles_pydantic_models() -> None:
    """Test that the decoder we use for SAQ will encode a pydantic model."""

    class Model(BaseModel):
        a: str
        b: int
        c: float

    pydantic_model = Model(a="a", b=1, c=2.34)
    encoded = worker.encoder.encode(pydantic_model)
    assert encoded == b'{"a":"a","b":1,"c":2.34}'


async def test_make_service_callback(
    raw_authors: list[dict[str, Any]], monkeypatch: MonkeyPatch
) -> None:
    """Tests loading and retrieval of service object types."""
    recv_cb_mock = AsyncMock()
    monkeypatch.setattr(service.Service, "receive_callback", recv_cb_mock, raising=False)
    await worker.make_service_callback(
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
        await worker.make_service_callback(
            {},
            service_type_id="tests.utils.domain.LSKDFJ",
            service_method_name="receive_callback",
            raw_obj=raw_authors[0],
        )


async def test_enqueue_service_callback(monkeypatch: MonkeyPatch) -> None:
    """Tests that job enqueued with desired arguments."""
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker.queue, "enqueue", enqueue_mock)
    service_instance = service.Service[Any]()
    await worker.enqueue_background_task_for_service(
        service_instance, "receive_callback", raw_obj={"a": "b"}
    )
    enqueue_mock.assert_called_once()
    assert isinstance(enqueue_mock.mock_calls[0].args[0], Job)
    job = enqueue_mock.mock_calls[0].args[0]
    assert job.function == worker.make_service_callback.__qualname__
    assert job.kwargs == {
        "service_type_id": "starlite_saqlalchemy.service.generic.Service",
        "service_method_name": "receive_callback",
        "raw_obj": {"a": "b"},
    }


async def test_enqueue_service_callback_with_custom_job_config(monkeypatch: MonkeyPatch) -> None:
    """Tests that job enqueued with desired arguments."""
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker.queue, "enqueue", enqueue_mock)
    service_instance = service.Service[Any]()
    await worker.enqueue_background_task_for_service(
        service_instance,
        "receive_callback",
        job_config=worker.JobConfig(timeout=999),
        raw_obj={"a": "b"},
    )
    enqueue_mock.assert_called_once()
    assert isinstance(enqueue_mock.mock_calls[0].args[0], Job)
    job = enqueue_mock.mock_calls[0].args[0]
    assert job.function == worker.make_service_callback.__qualname__
    assert job.timeout == 999
    assert job.kwargs == {
        "service_type_id": "starlite_saqlalchemy.service.generic.Service",
        "service_method_name": "receive_callback",
        "raw_obj": {"a": "b"},
    }
