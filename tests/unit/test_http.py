from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from starlite_saqlalchemy import http

if TYPE_CHECKING:

    from pytest import MonkeyPatch


async def test_client_request(monkeypatch: MonkeyPatch) -> None:
    """Tests logic of request() method."""
    response_mock = MagicMock()
    request_mock = AsyncMock(return_value=response_mock)
    monkeypatch.setattr(http.Client._client, "request", request_mock)
    res = await http.Client().request("with", "args", and_some="kwargs")
    request_mock.assert_called_once_with("with", "args", and_some="kwargs")
    response_mock.raise_for_status.assert_called_once()
    assert res is response_mock


async def test_client_raises_client_exception(monkeypatch: MonkeyPatch) -> None:
    """Tests that we convert httpx exceptions into ClientException."""
    exc = httpx.HTTPError("a message")
    req = AsyncMock(side_effect=exc)
    req.url = "http://whatever.com"
    exc.request = req
    monkeypatch.setattr(http.Client._client, "request", req)
    with pytest.raises(http.ClientException):
        await http.Client().request()


def test_client_json() -> None:
    """Tests the json() and unwrap_json() passthrough."""
    resp = MagicMock()
    resp.json.return_value = {"data": "data"}
    assert http.Client().json(resp) == {"data": "data"}
