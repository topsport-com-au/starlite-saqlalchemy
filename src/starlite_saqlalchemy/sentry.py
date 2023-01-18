"""Sentry config for our application."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlite import StarliteIntegration

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from starlite.types import HTTPScope


class SamplingContext(TypedDict):
    """Sentry context sent to traces sampler function."""

    asgi_scope: HTTPScope
    parent_sampled: bool | None
    transaction_context: dict[str, Any]


def sentry_traces_sampler(sampling_context: Mapping[str, Any]) -> float:
    """Don't send health check transactions to sentry."""
    sampling_context = cast("SamplingContext", sampling_context)
    if sampling_context["asgi_scope"]["path"] == settings.api.HEALTH_PATH:
        return 0.0
    return settings.sentry.TRACES_SAMPLE_RATE


def configure() -> None:
    """Configure sentry on app startup.

    See [SentrySettings][starlite_saqlalchemy.settings.SentrySettings].
    """
    sentry_sdk.init(
        dsn=settings.sentry.DSN,
        environment=settings.app.ENVIRONMENT,
        release=settings.app.BUILD_NUMBER,
        integrations=[StarliteIntegration(), SqlalchemyIntegration()],
        traces_sampler=sentry_traces_sampler,
    )
