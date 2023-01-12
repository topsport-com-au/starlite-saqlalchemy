"""Tests for application health check behavior."""
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from starlite.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.health import Health, HealthCheckProtocol, HealthController
from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyHealthCheck
from starlite_saqlalchemy.testing import modify_settings

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from starlite.testing import TestClient


def test_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    repo_health_mock = AsyncMock()
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    assert resp.json() == settings.app.dict()
    repo_health_mock.assert_called_once()


def test_health_check_false_response(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check response if check method returns `False`"""
    repo_health_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE


def test_health_check_exception_raised(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test expected response from check if exception raised in handler."""
    repo_health_mock = AsyncMock(side_effect=ConnectionError)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE


def test_health_custom_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test registering custom health checks."""

    class MyHealthCheck(HealthCheckProtocol):
        async def ready(self) -> bool:
            return False

        def error(self, _: Health) -> str:
            return "That's weird."

    HealthController.health_checks.append(MyHealthCheck())
    repo_health_mock = AsyncMock()
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    assert resp.json() == {"status_code": 503, "detail": "That's weird."}


@pytest.mark.parametrize(
    ("debug", "expected_error"),
    [(True, "Health check failed: MyHealthCheck.ready."), (False, "App is not ready.")],
)
def test_health_default_error(
    client: "TestClient", monkeypatch: "MonkeyPatch", debug: bool, expected_error: str
) -> None:
    """Test registering custom health checks."""

    class MyHealthCheck(HealthCheckProtocol):
        async def ready(self) -> bool:
            return False

    with modify_settings((settings.app, {"DEBUG": debug})):
        HealthController.health_checks.append(MyHealthCheck())
        repo_health_mock = AsyncMock()
        monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
        resp = client.get(settings.api.HEALTH_PATH)
        assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
        assert resp.json() == {"status_code": 503, "detail": expected_error}
