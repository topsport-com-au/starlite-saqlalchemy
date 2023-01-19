"""Tests for init_plugin.py."""
# pylint:disable=import-outside-toplevel
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from starlite import Starlite

from starlite_saqlalchemy import init_plugin
from starlite_saqlalchemy.constants import IS_SAQ_INSTALLED, IS_SENTRY_SDK_INSTALLED

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch


@pytest.mark.skipif(not IS_SAQ_INSTALLED, reason="saq is not installed")
def test_do_worker_but_not_logging(monkeypatch: MonkeyPatch) -> None:
    """Tests branch where we can have the worker enabled, but logging
    disabled."""
    from starlite_saqlalchemy import worker

    mock = MagicMock()
    monkeypatch.setattr(worker, "create_worker_instance", mock)
    config = init_plugin.PluginConfig(do_logging=False, do_worker=True)
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


@pytest.mark.skipif(not IS_SENTRY_SDK_INSTALLED, reason="sentry_sdk is not installed")
@pytest.mark.parametrize(
    ("env", "exp"), [("dev", True), ("prod", True), ("local", False), ("test", False)]
)
def test_sentry_environment_gate(env: str, exp: bool, monkeypatch: MonkeyPatch) -> None:
    """Test that the sentry integration is configured under different
    environment names."""
    from starlite_saqlalchemy import sentry

    monkeypatch.setattr(init_plugin, "IS_LOCAL_ENVIRONMENT", env == "local")
    monkeypatch.setattr(init_plugin, "IS_TEST_ENVIRONMENT", env == "test")
    app = Starlite(route_handlers=[], on_app_init=[init_plugin.ConfigureApp()])
    assert bool(sentry.configure in app.on_startup) is exp  # noqa: SIM901
