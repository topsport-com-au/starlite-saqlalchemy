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

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from starlite.testing import TestClient


def test_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    health_check = AppHealthCheck()
    monkeypatch.setattr(HealthController, "health_checks", [health_check])
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    health = HealthResource(app=settings.app, health={health_check.name: True})
    assert resp.json() == health.dict()


async def test_health_check_live() -> None:
    """Test expected result of calling `live()` health check method."""
    health_check = AppHealthCheck()
    assert await health_check.live() is True


def test_health_check_failed(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check response if check method returns `False`"""
    health_check = AppHealthCheck()
    monkeypatch.setattr(HealthController, "health_checks", [health_check])
    monkeypatch.setattr(health_check, "ready", AsyncMock(side_effect=RuntimeError))
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    HealthResource(app=settings.app, health={health_check.name: True})
    assert resp.json() == {
        "app": {
            "BUILD_NUMBER": "",
            "CHECK_DB_READY": True,
            "CHECK_REDIS_READY": True,
            "DEBUG": False,
            "ENVIRONMENT": "test",
            "TEST_ENVIRONMENT_NAME": "test",
            "LOCAL_ENVIRONMENT_NAME": "local",
            "NAME": "my-starlite-app",
        },
        "health": {"app": False},
    }


def test_health_custom_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test registering custom health checks."""
    class MyHealthCheck(AbstractHealthCheck):
        """Custom health check."""

        name = "MyHealthCheck"

        async def ready(self) -> bool:
            """Readiness check."""
            return False

    monkeypatch.setattr(HealthController, "health_checks", [AppHealthCheck(), MyHealthCheck()])
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={
            AppHealthCheck.name: True,
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
