"""Tests for init_plugin.py."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from starlite import Starlite

from starlite_saqlalchemy import init_plugin, worker

if TYPE_CHECKING:

    from pytest import MonkeyPatch


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
