"""Health check handler for the application.

Returns the app settings as details if successful, otherwise a 503.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel
from starlite import Controller, Response, get
from starlite.exceptions import ServiceUnavailableException

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.settings import AppSettings

if TYPE_CHECKING:
    from typing import Any

    from starlite import Request


class HealthCheckFailure(ServiceUnavailableException):
    """Raise for health check failure."""

    def __init__(
        self,
        health: dict[str, bool],
        *args: Any,
        detail: str = "",
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        """Initialize HealthCheckFailure with an additional health arg."""
        super().__init__(*args, detail, status_code, headers, extra)
        self.health = health


class AbstractHealthCheck(ABC):
    """Base protocol for implementing health checks."""

    name: str = ""

    async def live(self) -> bool:
        """Run a liveness check.

        Returns:
            True if the service is running, False otherwise
        """
        return await self.ready()  # pragma: no cover

    @abstractmethod
    async def ready(self) -> bool:
        """Run readiness check.

        Returns:
            True if the service is ready to serve requests, False otherwise
        """


class AppHealthCheck(AbstractHealthCheck):
    """Simple health check that does not require any dependencies."""

    name = "app"

    async def ready(self) -> bool:
        """Readiness check used when no other health check is available."""
        return True


class HealthResource(BaseModel):
    """Health data returned by the health endpoint."""

    app: AppSettings
    health: dict[str, bool]


def health_failure_exception_handler(
    _: Request, exc: HealthCheckFailure
) -> Response[HealthResource]:
    """Return all health checks data on `HealthCheckFailure`."""
    return Response(
        status_code=HealthCheckFailure.status_code,
        content=HealthResource(app=settings.app, health=exc.health),
    )


class HealthController(Controller):
    """Holds health endpoints."""

    exception_handlers = {HealthCheckFailure: health_failure_exception_handler}
    health_checks: list[AbstractHealthCheck] = []

    @get(path=settings.api.HEALTH_PATH, tags=["Misc"], raises=[HealthCheckFailure])
    async def health_check(self) -> HealthResource:
        """Run registered health checks."""
        health: dict[str, bool] = {}
        for health_check in self.health_checks:
            try:
                health[health_check.name] = await health_check.ready()
            except Exception:  # pylint: disable=broad-except
                health[health_check.name] = False
        if not all(health.values()):
            raise HealthCheckFailure(health=health)
        return HealthResource(app=settings.app, health=health)
