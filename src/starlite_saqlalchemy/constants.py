"""Application constants."""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from starlite_saqlalchemy.settings import app
from starlite_saqlalchemy.utils import case_insensitive_string_compare

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from starlite_saqlalchemy.service import Service


IS_TEST_ENVIRONMENT = case_insensitive_string_compare(app.ENVIRONMENT, app.TEST_ENVIRONMENT_NAME)
"""Flag indicating if the application is running in a test environment."""

IS_LOCAL_ENVIRONMENT = case_insensitive_string_compare(app.ENVIRONMENT, app.LOCAL_ENVIRONMENT_NAME)
"""Flag indicating if application is running in local development mode."""

IS_REDIS_INSTALLED = True
"""Flag indicating if redis module is installed."""

IS_SAQ_INSTALLED = True
"""Flag indicating if saq module is installed."""

IS_SENTRY_SDK_INSTALLED = True
"""Flag indicating if sentry_sdk module is installed."""

IS_SQLALCHEMY_INSTALLED = True
"""Flag indicating if sqlalchemy module is installed."""


for package in ("redis", "saq", "sentry_sdk", "sqlalchemy"):
    try:
        import_module(package)
    except ModuleNotFoundError:
        match package:
            case "redis":
                IS_REDIS_INSTALLED = False
            case "saq":
                IS_SAQ_INSTALLED = False
            case "sentry_sdk":
                IS_SENTRY_SDK_INSTALLED = False
            case "sqlalchemy":  # pragma: no cover
                IS_SQLALCHEMY_INSTALLED = False

SERVICE_OBJECT_IDENTITY_MAP: MutableMapping[str, type[Service[Any]]] = {}
"""Used by the worker to lookup methods for service object callbacks."""
