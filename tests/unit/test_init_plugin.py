"""Tests for init_plugin.py."""
# pylint:disable=duplicate-code

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlite import Starlite
from starlite.cache import SimpleCacheBackend

from starlite_saqlalchemy import init_plugin
from starlite_saqlalchemy.constants import IS_REDIS_INSTALLED

if TYPE_CHECKING:
    from typing import Any


def test_config_switches() -> None:
    """Tests that the app produced with all config switches off is as we
    expect."""
    config = init_plugin.PluginConfig(
        do_after_exception=False,
        do_cache=False,
        do_compression=False,
        do_collection_dependencies=False,
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
    # client.close goes in there unconditionally atm
    assert len(app.on_shutdown) == 1 if IS_REDIS_INSTALLED is False else 2
    assert not app.after_exception
    assert not app.dependencies
    assert not app.exception_handlers
    assert not app.on_startup
    assert not app.plugins
    assert not app.routes


@pytest.mark.parametrize(
    ("in_", "out"),
    [
        (["something"], ["something"]),
        ("something", ["something"]),
        ([], []),
        (None, []),
    ],
)
def test_ensure_list(in_: Any, out: Any) -> None:
    """Test _ensure_list() functionality."""
    # pylint: disable=protected-access
    assert init_plugin.ConfigureApp._ensure_list(in_) == out
