"""Tests for init_plugin.py."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from starlite import Starlite
from starlite.cache import SimpleCacheBackend

from starlite_saqlalchemy import init_plugin, sentry, worker

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
    assert len(app.on_shutdown) == 1
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
    monkeypatch.setattr(worker, "create_worker_instance", mock)
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
    app = Starlite(route_handlers=[], on_app_init=[init_plugin.ConfigureApp()])
    assert bool(sentry.configure in app.on_startup) is exp  # noqa: SIM901
