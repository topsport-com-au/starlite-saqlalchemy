"""Tests for `starlite_saqlalchemy.log module."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
import structlog
from starlite.status_codes import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from starlite.testing import RequestFactory
from structlog import DropEvent

from starlite_saqlalchemy import log, settings

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch
    from saq.job import Job
    from starlite import Starlite, State
    from starlite.types.asgi_types import (
        HTTPResponseBodyEvent,
        HTTPResponseStartEvent,
        HTTPScope,
    )
    from structlog.testing import CapturingLogger


@pytest.fixture(name="before_send_handler")
def fx_before_send_handler() -> log.controller.BeforeSendHandler:
    """Callable that receives send messages on their way out to the client."""
    return log.controller.BeforeSendHandler()


def test_drop_health_logs_raises_structlog_drop_event() -> None:
    """Health check shouldn't be logged if successful."""
    with pytest.raises(DropEvent):
        log.controller.drop_health_logs(
            None,
            "abc",
            {
                "event": settings.log.HTTP_EVENT,
                "request": {"path": settings.api.HEALTH_PATH},
                "response": {"status_code": HTTP_200_OK},
            },
        )


def test_drop_health_log_no_drop_event_if_not_success_status() -> None:
    """Healthcheck should be logged if it fails."""
    event_dict = {
        "event": settings.log.HTTP_EVENT,
        "request": {"path": settings.api.HEALTH_PATH},
        "response": {"status_code": HTTP_500_INTERNAL_SERVER_ERROR},
    }
    assert event_dict == log.controller.drop_health_logs(None, "abc", event_dict)


def test_middleware_factory_added_to_app(app: Starlite) -> None:
    """Ensures the plugin adds the middleware to clear the context."""
    assert log.controller.middleware_factory in app.middleware


async def test_middleware_calls_structlog_contextvars_clear_contextvars(
    monkeypatch: MonkeyPatch,
) -> None:
    """Ensure that we clear the structlog context in the middleware."""
    clear_ctx_vars_mock = MagicMock()
    monkeypatch.setattr(structlog.contextvars, "clear_contextvars", clear_ctx_vars_mock)
    app_mock = AsyncMock()
    middleware = log.controller.middleware_factory(app_mock)
    await middleware(1, 2, 3)  # type:ignore[arg-type]
    clear_ctx_vars_mock.assert_called_once()
    app_mock.assert_called_once_with(1, 2, 3)


@pytest.mark.parametrize(
    ("pattern", "excluded", "included"),
    [
        ("^/a", ["/a", "/abc", "/a/b/c"], ["/b", "/b/a"]),
        ("a$", ["/a", "/cba", "/c/b/gorilla"], ["/a/b/c", "/armadillo"]),
        ("/a|/b", ["/a", "/b", "/a/b", "/b/a", "/ab", "/ba"], ["/c", "/not-a", "/not-b"]),
    ],
)
async def test_before_send_handler_exclude_paths(
    pattern: str,
    excluded: list[str],
    included: list[str],
    before_send_handler: log.controller.BeforeSendHandler,
    http_response_start: HTTPResponseStartEvent,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """Test that exclude paths regex is respected.

    For each pattern, we ensure that each path in `excluded` is
    excluded, and each path in `included` is not excluded.
    """
    before_send_handler.exclude_paths = re.compile(pattern)

    async def call_handler(path_: str) -> dict[str, Any]:
        http_scope["path"] = path_
        http_scope["state"] = {}
        await before_send_handler(http_response_start, state, http_scope)
        return http_scope["state"]

    for path in excluded:
        assert {} == await call_handler(path)

    for path in included:
        scope_state = await call_handler(path)
        # scope state will be modified if path not excluded
        assert "log_level" in scope_state
        assert "http.response.start" in scope_state


@pytest.mark.parametrize(
    ("status", "level"),
    [
        (HTTP_200_OK, logging.INFO),
        (HTTP_500_INTERNAL_SERVER_ERROR, logging.ERROR),
    ],
)
async def test_before_send_handler_http_response_start(
    status: int,
    level: int,
    http_response_start: HTTPResponseStartEvent,
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """When handler receives a response start event, it should store the
    message in the connection state for later logging, and also use the status
    code to determine the severity of the eventual log."""
    http_response_start["status"] = status
    assert http_scope["state"] == {}
    await before_send_handler(http_response_start, state, http_scope)
    assert http_scope["state"]["log_level"] == level
    assert http_scope["state"]["http.response.start"] == http_response_start


async def test_before_send_handler_http_response_body_with_more_body(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    http_response_body["more_body"] = True
    await before_send_handler(http_response_body, state, http_scope)
    assert [] == cap_logger.calls


async def test_before_send_handler_http_response_body_without_more_body(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
    monkeypatch: MonkeyPatch,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    log_request_mock = AsyncMock()
    log_response_mock = AsyncMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_request", log_request_mock)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_response", log_response_mock)
    # this would have been added by the response start event handling
    http_scope["state"]["log_level"] = logging.INFO

    assert http_response_body["more_body"] is False
    await before_send_handler(http_response_body, state, http_scope)

    log_request_mock.assert_called_once_with(http_scope)
    log_response_mock.assert_called_once_with(http_scope)
    assert cap_logger.calls


async def test_before_send_handler_http_response_body_without_more_body_do_log_request_false(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
    monkeypatch: MonkeyPatch,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    log_request_mock = AsyncMock()
    log_response_mock = AsyncMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_request", log_request_mock)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_response", log_response_mock)
    # this would have been added by the response start event handling
    http_scope["state"]["log_level"] = logging.INFO

    assert http_response_body["more_body"] is False
    before_send_handler.do_log_request = False
    before_send_handler.do_log_response = False
    await before_send_handler(http_response_body, state, http_scope)

    log_request_mock.assert_not_called()
    log_response_mock.assert_not_called()
    assert cap_logger.calls


async def test_before_send_handler_does_nothing_with_other_message_types(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """We are only interested in the `http.response.{start,body}` messages."""
    message = {"type": "cats.and.dogs"}
    await before_send_handler(message, state, http_scope)  # type:ignore[arg-type]
    assert [] == cap_logger.calls


async def test_before_send_handler_log_request(
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    monkeypatch: MonkeyPatch,
) -> None:
    """Checks that the `log_request()` method does what it should."""
    ret_val = {"a": "b"}
    extractor_mock = AsyncMock(return_value=ret_val)
    bind_mock = MagicMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "extract_request_data", extractor_mock)
    monkeypatch.setattr(structlog.contextvars, "bind_contextvars", bind_mock)
    await before_send_handler.log_request(http_scope)
    extractor_mock.assert_called_once()
    bind_mock.assert_called_once_with(request=ret_val)


async def test_before_send_handler_log_response(
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    monkeypatch: MonkeyPatch,
) -> None:
    """Checks that the `log_response()` method does what it should."""
    ret_val = {"a": "b"}
    extractor_mock = MagicMock(return_value=ret_val)
    bind_mock = MagicMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "extract_response_data", extractor_mock)
    monkeypatch.setattr(structlog.contextvars, "bind_contextvars", bind_mock)
    await before_send_handler.log_response(http_scope)
    extractor_mock.assert_called_once_with(scope=http_scope)
    bind_mock.assert_called_once_with(response=ret_val)


async def test_before_send_handler_extract_request_data(
    before_send_handler: log.controller.BeforeSendHandler,
) -> None:
    """I/O test for extract_request_data() method."""
    request = RequestFactory().post("/", data={"a": "b"})
    data = await before_send_handler.extract_request_data(request)
    assert data == {
        "path": "/",
        "method": "POST",
        "content_type": ("application/json", {}),
        "headers": {"content-length": "10", "content-type": "application/json"},
        "cookies": {},
        "query": {},
        "path_params": {},
        "body": {"a": "b"},
    }


def test_before_send_handler_extract_response_data(
    before_send_handler: log.controller.BeforeSendHandler,
    http_response_start: HTTPResponseStartEvent,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
) -> None:
    """I/O test for extract_response_data() method."""
    http_scope["state"]["http.response.start"] = http_response_start
    http_scope["state"]["http.response.body"] = http_response_body
    data = before_send_handler.extract_response_data(http_scope)
    assert data == {"status_code": 200, "cookies": {}, "headers": {}, "body": b"body"}


async def test_before_process_calls_structlog_contextvars_clear_contextvars(
    monkeypatch: MonkeyPatch,
) -> None:
    """Ensure that we clear the structlog context in the worker before_process
    hook."""
    clear_ctx_vars_mock = MagicMock()
    monkeypatch.setattr(structlog.contextvars, "clear_contextvars", clear_ctx_vars_mock)
    await log.worker.before_process({})
    clear_ctx_vars_mock.assert_called_once()


async def test_after_process(job: Job, cap_logger: CapturingLogger) -> None:
    """Tests extraction of job data, and eventual log."""
    await log.worker.after_process({"job": job})
    assert [
        (
            "info",
            (),
            {
                "function": "whatever",
                "kwargs": {"a": "b"},
                "key": ANY,
                "scheduled": 0,
                "attempts": 0,
                "completed": 0,
                "queued": 0,
                "started": 0,
                "result": None,
                "error": None,
                "event": "Worker",
                "level": "info",
                "timestamp": ANY,
            },
        )
    ] == cap_logger.calls


async def test_after_process_logs_at_error(job: Job, cap_logger: CapturingLogger) -> None:
    """Tests eventual log is at ERROR level if `job.error`."""
    job.error = "Yep, this is the traceback."
    await log.worker.after_process({"job": job})
    assert [
        (
            "error",
            (),
            {
                "function": "whatever",
                "kwargs": {"a": "b"},
                "key": ANY,
                "scheduled": 0,
                "attempts": 0,
                "completed": 0,
                "queued": 0,
                "started": 0,
                "result": None,
                "error": "Yep, this is the traceback.",
                "event": "Worker",
                "level": "error",
                "timestamp": ANY,
            },
        )
    ] == cap_logger.calls