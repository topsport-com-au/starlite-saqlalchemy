"""Tests for application health check behavior."""
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from starlite import Starlite
from starlite.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from starlite_saqlalchemy import init_plugin, settings
from starlite_saqlalchemy.exceptions import HealthCheckConfigurationError
from starlite_saqlalchemy.health import (
    AbstractHealthCheck,
    AppHealthCheck,
    HealthController,
    HealthResource,
)
from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyHealthCheck

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from starlite.testing import TestClient


def test_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    repo_health_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    health = HealthResource(
        app=settings.app,
        health={SQLAlchemyHealthCheck.name: True, AppHealthCheck.name: True},
    )
    assert resp.json() == health.dict()
    repo_health_mock.assert_called_once()


def test_health_check_false_response(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check response if check method returns `False`"""
    repo_health_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={SQLAlchemyHealthCheck.name: False, AppHealthCheck.name: True},
    )
    assert resp.json() == health.dict()


def test_health_check_exception_raised(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test expected response from check if exception raised in handler."""
    repo_health_mock = AsyncMock(side_effect=ConnectionError)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={SQLAlchemyHealthCheck.name: False, AppHealthCheck.name: True},
    )
    assert resp.json() == health.dict()


def test_health_custom_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test registering custom health checks."""

    class MyHealthCheck(AbstractHealthCheck):
        """Custom health check."""

        name = "MyHealthCheck"

        async def ready(self) -> bool:
            """Readiness check."""
            return False

    HealthController.health_checks.append(MyHealthCheck())
    repo_health_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={
            AppHealthCheck.name: True,
            SQLAlchemyHealthCheck.name: True,
            MyHealthCheck.name: False,
        },
    )
    assert resp.json() == health.dict()


def test_health_check_no_name_error() -> None:
    """Test registering an health check without specifying its name raise an
    error."""

    class MyHealthCheck(AbstractHealthCheck):
        """Custom health check."""

        async def ready(self) -> bool:
            """Readiness check."""
            return False

    config = init_plugin.PluginConfig(health_checks=[MyHealthCheck])
    with pytest.raises(HealthCheckConfigurationError):
        Starlite(route_handlers=[], on_app_init=[init_plugin.ConfigureApp(config=config)])
