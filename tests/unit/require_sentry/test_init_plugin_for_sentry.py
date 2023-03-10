"""Tests for init_plugin.py."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import sentry_sdk
from sentry_sdk.integrations.starlite import SentryStarliteASGIMiddleware
from sentry_sdk.integrations.starlite import (
    exception_handler as sentry_after_exception_handler,
)
from starlite import Starlite
from starlite.handlers import BaseRouteHandler
from starlite.routes.http import HTTPRoute

from starlite_saqlalchemy import init_plugin, sentry

if TYPE_CHECKING:
    from pytest import MonkeyPatch
    from sentry_sdk._types import TracesSampler

    from starlite_saqlalchemy.sentry import SamplingContext


def _custom_traces_sampler(_: SamplingContext) -> float:
    return 0.42


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


@pytest.mark.parametrize(
    ("traces_sampler", "exp_traces_sampler"),
    [(None, sentry.sentry_traces_sampler), (_custom_traces_sampler, _custom_traces_sampler)],
)
def test_sentry_init(
    traces_sampler: TracesSampler | None,
    exp_traces_sampler: TracesSampler | None,
    monkeypatch: MonkeyPatch,
) -> None:
    sentry_init_mock = MagicMock()
    monkeypatch.setattr(sentry_sdk, "init", sentry_init_mock)
    init_plugin.ConfigureApp(
        config=init_plugin.PluginConfig(do_sentry=True, sentry_traces_sampler=traces_sampler)
    )
    sentry_init_mock.assert_called_once()
    assert sentry_init_mock.call_args.kwargs["traces_sampler"] is exp_traces_sampler
