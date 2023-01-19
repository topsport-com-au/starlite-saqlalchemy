"""Tests for init_plugin.py when no extra dependencies are installed."""

import pytest
from pydantic import ValidationError
from starlite import Starlite
from starlite.cache import SimpleCacheBackend

from starlite_saqlalchemy import init_plugin


def test_config_switches() -> None:
    """Tests that the app produced with all config switches off is as we
    expect."""
    config = init_plugin.PluginConfig(
        do_after_exception=False,
        do_cache=False,
        do_compression=False,
        # pyright reckons this parameter doesn't exist, I beg to differ
        do_collection_dependencies=False,  # pyright:ignore
        do_exception_handlers=False,
        do_health_check=False,
        do_logging=False,
        do_openapi=False,
        do_sentry=False,
        do_set_debug=False,
        do_sqlalchemy_plugin=False,
        do_type_encoders=False,
        do_worker=False,
    )
    app = Starlite(
        route_handlers=[],
        openapi_config=None,
        on_app_init=[init_plugin.ConfigureApp(config=config)],
    )
    assert app.compression_config is None
    assert app.debug is False
    assert app.logging_config is None
    assert app.openapi_config is None
    assert app.response_class is None
    assert isinstance(app.cache.backend, SimpleCacheBackend)
    assert len(app.on_shutdown) == 1
    assert not app.after_exception
    assert not app.dependencies
    assert not app.exception_handlers
    assert not app.on_startup
    assert not app.plugins
    assert not app.routes


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
