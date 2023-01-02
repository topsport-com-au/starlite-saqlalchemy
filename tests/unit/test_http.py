"""Tests for http.py."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from starlite_saqlalchemy import http

if TYPE_CHECKING:

    from pytest import MonkeyPatch


@pytest.fixture(name="client")
def fx_client() -> http.Client:
    """Mock client."""
    return http.Client(base_url="https://something.com")


async def test_client_request(client: http.Client, monkeypatch: MonkeyPatch) -> None:
    """Tests logic of request() method."""
    response_mock = MagicMock()
    request_mock = AsyncMock(return_value=response_mock)
    monkeypatch.setattr(client.client, "request", request_mock)
    res = await client.request("GET", "/here")
    request_mock.assert_called_once_with("GET", "/here", params=None, content=None, headers=None)
    response_mock.raise_for_status.assert_called_once()
    assert res is response_mock


async def test_client_raises_client_exception(
    client: http.Client, monkeypatch: MonkeyPatch
) -> None:
    """Tests that we convert httpx exceptions into ClientException."""
    exc = httpx.HTTPError("a message")
    req = AsyncMock(side_effect=exc)
    req.url = "http://whatever.com"
    exc.request = req
    monkeypatch.setattr(client.client, "request", req)
    with pytest.raises(http.ClientException):
        await client.request("GET", "/here")


def test_client_adds_headers_to_httpx_client() -> None:
    """Test headers are added to underlying client."""
    client = http.Client("http://localhost", headers={"X-Api-Key": "abc123"})
    assert "x-api-key" in client.client.headers


async def test_client_get(client: http.Client, monkeypatch: MonkeyPatch) -> None:
    """Test client GET call."""
    request_mock = AsyncMock()
    monkeypatch.setattr(http.Client, "request", request_mock)
    await client.get("/a", {"b": "c"}, {"d": "e"})
    request_mock.assert_called_once_with("GET", "/a", params={"b": "c"}, headers={"d": "e"})


async def test_client_post(client: http.Client, monkeypatch: MonkeyPatch) -> None:
    """Test client POST call."""
    request_mock = AsyncMock()
    monkeypatch.setattr(http.Client, "request", request_mock)
    await client.post("/a", b"bc", {"d": "e"})
    request_mock.assert_called_once_with("POST", "/a", content=b"bc", headers={"d": "e"})


async def test_client_put(client: http.Client, monkeypatch: MonkeyPatch) -> None:
    """Test client PUT call."""
    request_mock = AsyncMock()
    monkeypatch.setattr(http.Client, "request", request_mock)
    await client.put("/a", b"bc", {"d": "e"})
    request_mock.assert_called_once_with("PUT", "/a", content=b"bc", headers={"d": "e"})


async def test_client_delete(client: http.Client, monkeypatch: MonkeyPatch) -> None:
    """Test client DELETE call."""
    request_mock = AsyncMock()
    monkeypatch.setattr(http.Client, "request", request_mock)
    await client.delete("/a", {"d": "e"})
    request_mock.assert_called_once_with("DELETE", "/a", headers={"d": "e"})
