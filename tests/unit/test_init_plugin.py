"""Tests for init_plugin.py."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from sentry_sdk.integrations.starlite import SentryStarliteASGIMiddleware
from sentry_sdk.integrations.starlite import (
    exception_handler as sentry_after_exception_handler,
)
from starlite import Starlite
from starlite.cache import SimpleCacheBackend
from starlite.handlers import BaseRouteHandler
from starlite.routes.http import HTTPRoute

from starlite_saqlalchemy import init_plugin, sentry

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch


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
    # client.close and redis.close go in there unconditionally atm
    assert len(app.on_shutdown) == 2
    assert not app.after_exception
    assert not app.dependencies
    assert not app.exception_handlers
    assert not app.on_startup
    assert not app.plugins
    assert not app.routes


def test_do_worker_but_not_logging(monkeypatch: MonkeyPatch) -> None:
    """Tests branch where we can have the worker enabled, but logging
    disabled."""
    mock = MagicMock()
    monkeypatch.setattr(init_plugin, "create_worker_instance", mock)
    config = init_plugin.PluginConfig(do_logging=False)
    Starlite(route_handlers=[], on_app_init=[init_plugin.ConfigureApp(config=config)])
    mock.assert_called_once()
    call = mock.mock_calls[0]
    assert "before_process" not in call.kwargs
    assert "after_process" not in call.kwargs


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


@pytest.mark.parametrize(
    ("env", "exp"), [("dev", True), ("prod", True), ("local", False), ("test", False)]
)
def test_sentry_environment_gate(env: str, exp: bool, monkeypatch: MonkeyPatch) -> None:
    """Test that the sentry integration is configured under different
    environment names."""
    monkeypatch.setattr(init_plugin, "IS_LOCAL_ENVIRONMENT", env == "local")
    monkeypatch.setattr(init_plugin, "IS_TEST_ENVIRONMENT", env == "test")
    mock = MagicMock()
    monkeypatch.setattr(sentry, "configure", mock)
    Starlite(route_handlers=[], on_app_init=[init_plugin.ConfigureApp()])
    assert mock.call_count == int(exp)


def test_do_sentry() -> None:
    """Test that do_sentry flag correctly patch Starlite."""
    old_init = Starlite.__init__
    old_route_handle = HTTPRoute.handle
    old_resolve_middleware = BaseRouteHandler.resolve_middleware

    app = Starlite(
        route_handlers=[],
        on_app_init=[init_plugin.ConfigureApp(config=init_plugin.PluginConfig(do_sentry=True))],
    )
    after_exception_handlers = []
    for handler in app.after_exception:
        handler_fn = handler.ref.value
        # If wrapped with `starlite.utils.async_partial`
        if hasattr(handler_fn, "func"):
            handler_fn = handler_fn.func
        after_exception_handlers.append(handler_fn)
    assert SentryStarliteASGIMiddleware in app.middleware  # type: ignore
    assert sentry_after_exception_handler in after_exception_handlers  # type: ignore

    Starlite.__init__ = old_init  # type: ignore
    HTTPRoute.handle = old_route_handle  # type: ignore
    BaseRouteHandler.resolve_middleware = old_resolve_middleware  # type: ignore
