"""All configuration via environment.

Take note of the environment variable prefixes required for each
settings class, except `AppSettings`.
"""
from __future__ import annotations

# pylint: disable=too-few-public-methods,missing-class-docstring
from typing import Literal

from pydantic import AnyUrl, BaseSettings, PostgresDsn
from starlite.utils.extractors import RequestExtractorField, ResponseExtractorField


# noinspection PyUnresolvedReferences
class AppSettings(BaseSettings):
    """Generic application settings.

    These settings are returned as json by the healthcheck endpoint, so
    do not include any sensitive values here, or if you do ensure to
    exclude them from serialization in the `Config` object.
    """

    class Config:
        case_sensitive = True
        env_file = ".env"

    BUILD_NUMBER: str = ""
    """Identifier for CI build."""
    DEBUG: bool = False
    """Run `Starlite` with `debug=True`."""
    ENVIRONMENT: str = "prod"
    """'dev', 'prod', etc."""
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
        case_sensitive = True
        env_file = ".env"
        env_prefix = "API_"

    CACHE_EXPIRATION: int = 60
    """Default cache key expiration in seconds."""
    DB_SESSION_DEPENDENCY_KEY: str = "db_session"
    """Parameter name for SQLAlchemy session dependency injection."""
    DEFAULT_PAGINATION_LIMIT: int = 100
    """Max records received for collection routes."""
    DTO_INFO_KEY: str = "dto"
    """Key used for DTO field config in SQLAlchemy info dict."""
    HEALTH_PATH: str = "/health"
    """Route that the health check is served under."""


class LogSettings(BaseSettings):
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "LOG_"

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Starlite handlers."""
    LEVEL: int = 20
    """Stdlib log levels. Only emit logs at this level, or higher."""
    OBFUSCATE_COOKIES: set[str] = {"session"}
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = {"Authorization", "X-API-KEY"}
    """Request header keys to obfuscate."""
    JOB_FIELDS: list[str] = [
        "function",
        "kwargs",
        "key",
        "scheduled",
        "attempts",
        "completed",
        "queued",
        "started",
        "result",
        "error",
    ]
    """Attributes of the SAQ [`Job`](https://github.com/tobymao/saq/blob/master/saq/job.py)
    to be logged.
    """
    REQUEST_FIELDS: list[RequestExtractorField] = [
        "path",
        "method",
        "content_type",
        "headers",
        "cookies",
        "query",
        "path_params",
        "body",
    ]
    """Attributes of the [Request][starlite.connection.request.Request] to be logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = [
        "status_code",
        "cookies",
        "headers",
        "body",
    ]
    """Attributes of the [Response][starlite.response.Response] to be logged."""
    WORKER_EVENT: str = "Worker"
    """Log event name for logs from SAQ worker."""


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """Configures OpenAPI for the application.

    Prefix all environment variables with `OPENAPI_`, e.g.,
    `OPENAPI_TITLE`.
    """

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "OPENAPI_"

    CONTACT_NAME: str
    """Name of contact on document."""
    CONTACT_EMAIL: str
    """Email for contact on document."""
    TITLE: str | None
    """Document title."""
    VERSION: str
    """Document version."""


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
        case_sensitive = True
        env_file = ".env"
        env_prefix = "DB_"

    ECHO: bool = False
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool | Literal["debug"] = False
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLE: bool = False
    """Disable SQLAlchemy pooling, same as setting pool to
    [`NullPool`][sqlalchemy.pool.NullPool].
    """
    POOL_MAX_OVERFLOW: int = 10
    """See [`max_overflow`][sqlalchemy.pool.QueuePool]."""
    POOL_SIZE: int = 5
    """See [`pool_size`][sqlalchemy.pool.QueuePool]."""
    POOL_TIMEOUT: int = 30
    """See [`timeout`][sqlalchemy.pool.QueuePool]."""
    URL: PostgresDsn


# noinspection PyUnresolvedReferences
class RedisSettings(BaseSettings):
    """Cache settings for the application.

    Prefix all environment variables with `REDIS_`, e.g., `REDIS_URL`.
    """

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "REDIS_"

    URL: AnyUrl
    """A Redis connection URL."""


# noinspection PyUnresolvedReferences
class SentrySettings(BaseSettings):
    """Configures sentry for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "SENTRY_"

    DSN: str = ""
    """The sentry DSN. Set as empty string to disable sentry reporting."""
    TRACES_SAMPLE_RATE: float = 0.0001
    """% of requests traced by sentry, `0.0` means none, `1.0` means all."""


class ServerSettings(BaseSettings):
    """Server configurations."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "SERVER_"

    APP_LOC: str = "app.main:create_app"
    APP_LOC_IS_FACTORY: bool = True
    HOST: str = "localhost"
    KEEPALIVE: int = 65
    PORT: int = 8000
    RELOAD: bool = False
    RELOAD_DIRS: list[str] = ["src/"]


# `.parse_obj()` thing is a workaround for pyright and pydantic interplay, see:
# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
api = APISettings.parse_obj({})
"""Api settings."""
app = AppSettings.parse_obj({})
"""App settings."""
db = DatabaseSettings.parse_obj({})
"""Database settings."""
log = LogSettings.parse_obj({})
"""Log settings."""
openapi = OpenAPISettings.parse_obj({})
"""Openapi settings."""
redis = RedisSettings.parse_obj({})
"""Redis settings."""
sentry = SentrySettings.parse_obj({})
"""Sentry settings."""
server = ServerSettings.parse_obj({})
"""Server settings."""
