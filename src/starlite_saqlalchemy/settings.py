"""All configuration via environment.

Take note of the environment variable prefixes required for each
settings class, except `AppSettings`.
"""
from __future__ import annotations

# pylint: disable=missing-class-docstring
from typing import Literal

from pydantic import AnyUrl, BaseSettings, PostgresDsn, parse_obj_as
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
    NAME: str = "my-starlite-saqlalchemy-app"
    """Application name."""

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return "-".join(s.lower() for s in self.NAME.split())


# noinspection PyUnresolvedReferences
class APISettings(BaseSettings):
    """API specific configuration."""

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
    """Logging config for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "LOG_"

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Starlite handlers."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
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
    SAQ_LEVEL: int = 30
    """Level to log SAQ logs."""
    SQLALCHEMY_LEVEL: int = 30
    """Level to log SAQ logs."""
    UVICORN_ACCESS_LEVEL: int = 30
    """Level to log uvicorn access logs."""
    UVICORN_ERROR_LEVEL: int = 30
    """Level to log uvicorn error logs."""


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """Configures OpenAPI for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "OPENAPI_"

    CONTACT_NAME: str = "Peter"
    """Name of contact on document."""
    CONTACT_EMAIL: str = "peter.github@proton.me"
    """Email for contact on document."""
    TITLE: str | None = "My Starlite-SAQAlchemy App"
    """Document title."""
    VERSION: str = "v1.0"
    """Document version."""


# noinspection PyUnresolvedReferences
class DatabaseSettings(BaseSettings):
    """Configures the database for the application."""

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
    URL: PostgresDsn = parse_obj_as(
        PostgresDsn, "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres"
    )


# noinspection PyUnresolvedReferences
class RedisSettings(BaseSettings):
    """Redis settings for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "REDIS_"

    URL: AnyUrl = parse_obj_as(AnyUrl, "redis://localhost:6379/0")
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
    """Path to app executable, or factory."""
    APP_LOC_IS_FACTORY: bool = True
    """Indicate if APP_LOC points to an executable or factory."""
    HOST: str = "localhost"
    """Server network host."""
    KEEPALIVE: int = 65
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    PORT: int = 8000
    """Server port."""
    RELOAD: bool = False
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = ["src/"]
    """Directories to watch for reloading."""


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
