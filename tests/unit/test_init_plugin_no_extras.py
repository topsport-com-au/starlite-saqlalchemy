"""Tests for init_plugin.py when no extra dependencies are installed."""

import pytest
from pydantic import ValidationError

from starlite_saqlalchemy import constants, init_plugin

SKIP = any(
    [
        constants.IS_SAQ_INSTALLED,
        constants.IS_SENTRY_SDK_INSTALLED,
        constants.IS_REDIS_INSTALLED,
        constants.IS_SQLALCHEMY_INSTALLED,
    ]
)


@pytest.mark.skipif(SKIP, reason="test will only run if no extras are installed")
@pytest.mark.parametrize(
    ("enabled_config", "error_pattern"),
    [
        ("do_cache", r"\'redis\' is not installed."),
        ("do_sentry", r"\'sentry_sdk\' is not installed."),
        ("do_worker", r"\'saq\' is not installed."),
        ("do_sqlalchemy_plugin", r"\'sqlalchemy\' is not installed."),
    ],
)
def test_extra_dependencies_not_installed(enabled_config: str, error_pattern: str) -> None:
    """Tests that the plugin test required dependencies for switches needing
    them."""
    kwargs = {
        "do_after_exception": False,
        "do_cache": False,
        "do_compression": False,
        "do_collection_dependencies": False,
        "do_exception_handlers": False,
        "do_health_check": False,
        "do_logging": False,
        "do_openapi": False,
        "do_sentry": False,
        "do_set_debug": False,
        "do_sqlalchemy_plugin": False,
        "do_type_encoders": False,
        "do_worker": False,
        **{enabled_config: True},
    }
    with pytest.raises(ValidationError, match=error_pattern):
        init_plugin.PluginConfig(**kwargs)
