"""Tests for application health check behavior."""
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from starlite.status_codes import HTTP_200_OK

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.health import HealthController, HealthResource
from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyHealthCheck

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from starlite.testing import TestClient


def test_health_check(client: "TestClient", monkeypatch: "MonkeyPatch") -> None:
    """Test health check success response.

    Checks that we call the repository method and the response content.
    """
    health_check = SQLAlchemyHealthCheck()
    monkeypatch.setattr(HealthController, "health_checks", [health_check])
    repo_health_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(health_check, "ready", repo_health_mock)
    resp = client.get(settings.api.HEALTH_PATH)
    assert resp.status_code == HTTP_200_OK
    health = HealthResource(app=settings.app, health={health_check.name: True})
    assert resp.json() == health.dict()
    repo_health_mock.assert_called_once()
