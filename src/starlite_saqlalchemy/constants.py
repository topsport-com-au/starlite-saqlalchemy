"""Application constants."""
from __future__ import annotations

from starlite_saqlalchemy.settings import app
from starlite_saqlalchemy.utils import case_insensitive_string_compare

IS_TEST_ENVIRONMENT = case_insensitive_string_compare(app.ENVIRONMENT, app.TEST_ENVIRONMENT_NAME)
"""Flag indicating if the application is running in a test environment."""

IS_LOCAL_ENVIRONMENT = case_insensitive_string_compare(app.ENVIRONMENT, app.LOCAL_ENVIRONMENT_NAME)
"""Flag indicating if application is running in local development mode."""
