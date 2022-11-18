"""Sentry config for our application.

The current support for sentry is limited, but still worth having.

See: https://github.com/getsentry/sentry-python/issues/1549
"""
from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from starlite_saqlalchemy import settings


def configure() -> None:
    """Configure sentry on app startup.

    See [SentrySettings][starlite_saqlalchemy.settings.SentrySettings].
    """
    sentry_sdk.init(
        dsn=settings.sentry.DSN,
        environment=settings.app.ENVIRONMENT,
        release=settings.app.BUILD_NUMBER,
        integrations=[SqlalchemyIntegration()],
        traces_sample_rate=settings.sentry.TRACES_SAMPLE_RATE,
    )
