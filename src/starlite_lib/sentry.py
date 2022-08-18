import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .config import app_settings, sentry_settings


def configure() -> None:
    """
    Callback to configure sentry on app startup.

    See [SentrySettings][starlite_lib.config.SentrySettings].
    """
    sentry_sdk.init(
        dsn=sentry_settings.DSN,
        environment=app_settings.ENVIRONMENT,
        release=app_settings.BUILD_NUMBER,
        integrations=[SqlalchemyIntegration()],
        traces_sample_rate=sentry_settings.TRACES_SAMPLE_RATE,
    )
