"""All configuration via environment.

Take note of the environment variable prefixes required for each
settings class, except `AppSettings`.
"""
# pylint: disable=too-few-public-methods,missing-class-docstring
from typing import Literal

from pydantic import AnyUrl, BaseSettings, PostgresDsn


# noinspection PyUnresolvedReferences
class AppSettings(BaseSettings):
    """Generic application settings.

    These settings are returned as json by the healthcheck endpoint, so
    do not include any sensitive values here, or if you do ensure to
    exclude them from serialization in the `Config` object.
    """

    class Config:
        case_sensitive = True

    BUILD_NUMBER: str
    """Identifier for CI build."""
    DEBUG: bool
    """Run `Starlite` with `debug=True`."""
    ENVIRONMENT: str
    """'dev', 'prod', etc."""
    LOG_LEVEL: str
    """Stdlib log level names, 'DEBUG', 'INFO', etc."""
    NAME: str
    """Application name."""

    @property
    def slug(self) -> str:
        """A slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return "-".join(s.lower() for s in self.NAME.split())


# noinspection PyUnresolvedReferences
class APISettings(BaseSettings):
    """API specific configuration.

    Prefix all environment variables with `API_`, e.g.,
    `API_CACHE_EXPIRATION`.
    """

    class Config:
        env_prefix = "API_"
        case_sensitive = True

    CACHE_EXPIRATION: int
    """Default cache key expiration in seconds."""
    DB_SESSION_DEPENDENCY_KEY: str
    """Parameter name for SQLAlchemy session dependency injection."""
    DEFAULT_PAGINATION_LIMIT: int
    """Max records received for collection routes."""
    HEALTH_PATH: str
    """Route that the health check is served under."""


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """Configures OpenAPI for the application.

    Prefix all environment variables with `OPENAPI_`, e.g.,
    `OPENAPI_TITLE`.
    """

    class Config:
        env_prefix = "OPENAPI_"
        case_sensitive = True

    TITLE: str | None
    """Document title."""
    VERSION: str
    """Document version."""
    CONTACT_NAME: str
    """Name of contact on document."""
    CONTACT_EMAIL: str
    """Email for contact on document."""


# noinspection PyUnresolvedReferences
class DatabaseSettings(BaseSettings):
    """Configures the database for the application.

    Prefix all environment variables with `DB_`, e.g., `DB_URL`.

    Attributes
    ----------
    ECHO : bool
        Enables SQLAlchemy engine logs.
    URL : PostgresDsn
        URL for database connection.
    """

    class Config:
        env_prefix = "DB_"
        case_sensitive = True

    ECHO: bool
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool | Literal["debug"]
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLE: bool
    """Disable SQLAlchemy pooling, same as setting pool to
    [`NullPool`][sqlalchemy.pool.NullPool].
    """
    POOL_MAX_OVERFLOW: int
    """See [`max_overflow`][sqlalchemy.pool.QueuePool.max_overflow]."""
    POOL_SIZE: int
    """See [`pool_size`][sqlalchemy.pool.QueuePool.pool_size]."""
    POOL_TIMEOUT: int
    """See [`timeout`][sqlalchemy.pool.QueuePool.timeout]."""
    URL: PostgresDsn


# noinspection PyUnresolvedReferences
class RedisSettings(BaseSettings):
    """Cache settings for the application.

    Prefix all environment variables with `REDIS_`, e.g., `REDIS_URL`.
    """

    class Config:
        env_prefix = "REDIS_"
        case_sensitive = True

    URL: AnyUrl
    """A Redis connection URL."""


# noinspection PyUnresolvedReferences
class SentrySettings(BaseSettings):
    """Configures sentry for the application."""

    class Config:
        env_prefix = "SENTRY_"
        case_sensitive = True

    DSN: str
    """The sentry DSN. Set as empty string to disable sentry reporting."""
    TRACES_SAMPLE_RATE: float
    """% of requests traced by sentry, `0.0` means none, `1.0` means all."""


# `.parse_obj()` thing is a workaround for pyright and pydantic interplay, see:
# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
api = APISettings.parse_obj({})
"""Api settings."""
app = AppSettings.parse_obj({})
"""App settings."""
db = DatabaseSettings.parse_obj({})
"""Database settings."""
openapi = OpenAPISettings.parse_obj({})
"""Openapi settings."""
redis = RedisSettings.parse_obj({})
"""Redis settings."""
sentry = SentrySettings.parse_obj({})
"""Sentry settings."""
