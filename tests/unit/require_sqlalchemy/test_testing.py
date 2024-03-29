"""Test testing module."""
# pylint: disable=wrong-import-position,wrong-import-order
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import httpx
import pytest
from starlite.status_codes import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from starlite_saqlalchemy import testing
from tests.utils.domain.authors import Service as AuthorService

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch
    from starlite import TestClient

    from tests.utils.domain.authors import Author


@pytest.fixture(name="mock_response")
def fx_mock_response() -> MagicMock:
    """Mock response for returning from mock client requests."""
    return MagicMock(spec_set=dir(httpx.Response) + ["status_code"], status_code=HTTP_200_OK)


@pytest.fixture(name="mock_request")
def fx_mock_request(mock_response: MagicMock) -> MagicMock:
    """Mock 'request' method for client."""
    return MagicMock(return_value=mock_response)


@pytest.fixture(name="mock_client")
def fx_mock_client(
    client: TestClient, mock_request: MagicMock, monkeypatch: MonkeyPatch
) -> TestClient:
    """Patches the test client with a mock 'request' method."""
    monkeypatch.setattr(client, "request", mock_request)
    return client


@pytest.fixture(name="tester")
def fx_tester(
    authors: list[Author],
    raw_authors: list[dict[str, Any]],
    mock_client: TestClient,
    monkeypatch: MonkeyPatch,
    mock_response: MagicMock,
) -> testing.ControllerTest:
    """Tester fixture."""
    mock_response.json.return_value = raw_authors[0]
    return testing.ControllerTest(
        client=mock_client,
        base_path="/authors",
        collection=authors[:1],
        raw_collection=raw_authors[:1],
        service_type=AuthorService,
        monkeypatch=monkeypatch,
    )


async def test_tester_get_collection_request_service_method_patch(
    tester: testing.ControllerTest, mock_response: MagicMock
) -> None:
    """Test that the "list" service method has been patched."""

    mock_response.json.return_value = tester.raw_collection
    tester.test_get_collection()
    assert "<locals>._list" in str(AuthorService.list)
    assert await AuthorService(session=None).list() == tester.collection


def test_tester_get_collection_raises_assertion_error_on_status_code(
    tester: testing.ControllerTest, mock_response: MagicMock
) -> None:
    """Test raising behavior when response status doesn't match expected."""
    mock_response.status_code = HTTP_404_NOT_FOUND
    with pytest.raises(AssertionError):
        tester.test_get_collection()


def test_tester_get_collection_raises_assertion_error_on_unexpected_json_response(
    tester: testing.ControllerTest, mock_response: MagicMock
) -> None:
    """Test raising behavior when json response doesn't match expected."""
    mock_response.json.return_value = []
    with pytest.raises(AssertionError):
        tester.test_get_collection()


def test_tester_get_collection_request_called_with_query_params(
    tester: testing.ControllerTest, mock_request: MagicMock, mock_response: MagicMock
) -> None:
    """Test makes request with query parameters."""
    mock_response.json.return_value = tester.raw_collection
    tester.collection_filters = {"a": "b"}
    tester.test_get_collection(with_filters=True)
    assert mock_request.mock_calls[0].kwargs["params"] == {"a": "b"}


def test_tester_test_member_request_post_request(
    tester: testing.ControllerTest,
    mock_request: MagicMock,
) -> None:
    """Test uses correct URL for post request."""
    tester.test_member_request("POST", "create", 200)
    call = mock_request.mock_calls[0]
    assert call.args[0] == "POST"
    assert call.args[1] == "/authors"


@pytest.mark.parametrize(("method", "service_method"), [("POST", "create"), ("PUT", "update")])
def test_tester_json_in_request_kwargs(
    method: str, service_method: str, tester: testing.ControllerTest, mock_request: MagicMock
) -> None:
    """Test adds "json" kwarg to requests for POST and PUT."""
    tester.test_member_request(method, service_method, 200)
    call = mock_request.mock_calls[0]
    assert "json" in call.kwargs


async def test_tester_member_request_service_method_patch(tester: testing.ControllerTest) -> None:
    """Test that the appropriate service method gets patched."""
    tester.test_member_request("GET", "get", 200)
    assert "<locals>._method" in str(AuthorService.get)
    assert await AuthorService(session=None).get(123) == tester.collection[0]


@pytest.mark.parametrize("params", [{"a": "b"}, None])
def test_tester_run_method(params: dict[str, Any] | None) -> None:
    """Test run method makes all expected calls."""
    self_mock = MagicMock(collection_filters=params)
    testing.ControllerTest.run(self_mock)
    if params:
        assert self_mock.mock_calls == [
            ("test_get_collection", (), {}),
            ("test_get_collection", (), {"with_filters": True}),
            ("test_member_request", ("GET", "get", 200), {}),
            ("test_member_request", ("PUT", "update", 200), {}),
            ("test_member_request", ("POST", "create", 201), {}),
            ("test_member_request", ("DELETE", "delete", 200), {}),
        ]
    else:
        assert self_mock.mock_calls == [
            ("test_get_collection", (), {}),
            ("test_member_request", ("GET", "get", 200), {}),
            ("test_member_request", ("PUT", "update", 200), {}),
            ("test_member_request", ("POST", "create", 201), {}),
            ("test_member_request", ("DELETE", "delete", 200), {}),
        ]


def test_tester_ignores_405_response(
    tester: testing.ControllerTest, mock_response: MagicMock
) -> None:
    """Test that 405 responses don't raise from asserts."""
    mock_response.status_code = HTTP_405_METHOD_NOT_ALLOWED
    tester.test_get_collection()
    tester.test_member_request("GET", "get", HTTP_200_OK)
