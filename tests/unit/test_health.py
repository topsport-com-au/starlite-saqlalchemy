"""Tests for application health check behavior."""
# pylint: disable=ungrouped-imports
from itertools import product
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from starlite import Starlite
from starlite.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from starlite_saqlalchemy import init_plugin, settings
from starlite_saqlalchemy.constants import IS_SQLALCHEMY_INSTALLED
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


health_checks: "list[AbstractHealthCheck]" = [AppHealthCheck()]

if IS_SQLALCHEMY_INSTALLED:
    from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyHealthCheck

    health_checks.append(SQLAlchemyHealthCheck())


@pytest.mark.parametrize("health_check", health_checks)
def test_health_check(
    client: "TestClient", monkeypatch: "MonkeyPatch", health_check: AbstractHealthCheck
) -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    monkeypatch.setattr(HealthController, "health_checks", health_checks)
    repo_health_mock = AsyncMock(return_value=True)
    for health_check_ in health_checks:
        monkeypatch.setattr(health_check_, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    health = HealthResource(
        app=settings.app,
        health={ht.name: True for ht in health_checks} | {health_check.name: True},
    )
    assert resp.json() == health.dict()
    assert repo_health_mock.call_count == len(health_checks)


@pytest.mark.parametrize(
    ("health_check", "mock"),
    product(health_checks, [AsyncMock(return_value=False), AsyncMock(side_effect=ConnectionError)]),
)
def test_health_check_failed(
    client: "TestClient",
    monkeypatch: "MonkeyPatch",
    health_check: AbstractHealthCheck,
    mock: AsyncMock,
) -> None:
    """Test health check response if check method returns `False`"""
    # repo_health_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(HealthController, "health_checks", health_checks)
    for health_check_ in health_checks:
        if health_check_ is health_check:
            monkeypatch.setattr(health_check_, "ready", mock)
        else:
            monkeypatch.setattr(health_check_, "ready", AsyncMock(return_value=True))
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={ht.name: True for ht in health_checks} | {health_check.name: False},
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

    monkeypatch.setattr(HealthController, "health_checks", [AppHealthCheck(), MyHealthCheck()])
    # repo_health_mock = AsyncMock(return_value=True)
    # monkeypatch.setattr(SQLAlchemyHealthCheck, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_503_SERVICE_UNAVAILABLE
    health = HealthResource(
        app=settings.app,
        health={
            AppHealthCheck.name: True,
            # SQLAlchemyHealthCheck.name: True,
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
