"""Health check handler for the application.

Returns the app settings as details if successful, otherwise a 503.
"""
from __future__ import annotations

import contextlib
from enum import Enum
from typing import Protocol

from starlite import Controller, get
from starlite.exceptions import ServiceUnavailableException

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.settings import AppSettings


class HealthCheckFailure(ServiceUnavailableException):
    """Raise for health check failure."""


class Health(Enum):
    """Health check types."""

    LIVE = "live"
    READY = "ready"


class HealthCheckProtocol(Protocol):
    """Base protocol for implementing health checks."""

    async def live(self) -> bool:
        """Run a liveness check.

        Returns:
            True if the service is running, False otherwise
        """

    async def ready(self) -> bool:
        """Run readiness check.

        Returns:
            True if the service is ready to serve requests, False otherwise
        """

    def error(self, target_health: Health) -> str:
        """Error message to return when health check fails.

        Args:
            target_health: Type of health check that failed

        Returns:
            A string describing the failure state
        """
        if settings.app.DEBUG:
            return f"Health check failed: {self.__class__.__name__}.{target_health.value}."
        return f"App is not {target_health.value}."


class HealthController(Controller):
    """Holds health endpoints."""

    health_checks: list[HealthCheckProtocol] = []

    @get(path=settings.api.HEALTH_PATH, tags=["Misc"], raises=[HealthCheckFailure])
    async def health_check(self) -> AppSettings:
        """Run registered health checks."""
        for health_check in self.health_checks:
            with contextlib.suppress(Exception):
                if await health_check.ready():
                    continue
            raise HealthCheckFailure(health_check.error(Health.READY))
        else:
            return settings.app
