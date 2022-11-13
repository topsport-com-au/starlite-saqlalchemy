"""Tests for application health check behavior."""
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from starlite.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from starlite.testing import TestClient


def test_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    repo_health_mock = AsyncMock()
    monkeypatch.setattr(SQLAlchemyRepository, "check_health", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    assert resp.json() == settings.app.dict()
    repo_health_mock.assert_called_once()


def test_health_check_false_response(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check response if check method returns `False`"""
    repo_health_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(SQLAlchemyRepository, "check_health", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE


def test_health_check_exception_raised(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test expected response from check if exception raised in handler."""
    repo_health_mock = AsyncMock(side_effect=ConnectionError)
    monkeypatch.setattr(SQLAlchemyRepository, "check_health", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
