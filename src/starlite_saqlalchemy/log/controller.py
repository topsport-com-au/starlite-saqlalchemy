"""Logging config for the application.

Ensures that the app, sqlalchemy, saq and uvicorn loggers all log through the queue listener.

Adds a filter for health check route logs.
"""
from __future__ import annotations

import logging
import re
from inspect import isawaitable
from typing import TYPE_CHECKING

import structlog
from starlite.enums import ScopeType
from starlite.utils.extractors import ConnectionDataExtractor, ResponseDataExtractor

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from typing import Any

    from starlite.connection import Request
    from starlite.datastructures import State
    from starlite.types.asgi_types import ASGIApp, Message, Receive, Scope, Send
    from structlog.types import EventDict, WrappedLogger

LOGGER = structlog.get_logger()


def drop_health_logs(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Prevent logging of successful health checks.

    Args:
        _: Wrapped logger object.
        __: Name of the wrapped method, e.g., "info", "warning", etc.
        event_dict: Current context with current event, e.g, `{"a": 42, "event": "foo"}`.

    Returns:
        `event_dict` for further processing if it does not represent a successful health check.
    """
    is_http_log = event_dict["event"] == settings.log.HTTP_EVENT
    is_health_log = event_dict.get("request", {}).get("path") == settings.api.HEALTH_PATH
    is_success_status = 200 <= event_dict.get("response", {}).get("status_code", 0) < 300
    if is_http_log and is_health_log and is_success_status:
        raise structlog.DropEvent
    return event_dict


def middleware_factory(app: ASGIApp) -> ASGIApp:
    """Middleware to ensure that every request has a clean structlog context.

    Args:
        app: The previous ASGI app in the call chain.

    Returns:
        A new ASGI app that cleans the structlog contextvars.
    """

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        """Cleans up the structlog contextvars.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive handler.
            send: ASGI send handler.
        """
        structlog.contextvars.clear_contextvars()
        await app(scope, receive, send)

    return middleware


class BeforeSendHandler:
    """Extraction of request and response data from connection scope."""

    __slots__ = (
        "do_log_request",
        "do_log_response",
        "exclude_paths",
        "logger",
        "request_extractor",
        "response_extractor",
    )

    def __init__(self) -> None:
        self.exclude_paths = re.compile(settings.log.EXCLUDE_PATHS)
        self.do_log_request = bool(settings.log.REQUEST_FIELDS)
        self.do_log_response = bool(settings.log.RESPONSE_FIELDS)
        self.request_extractor = ConnectionDataExtractor(
            extract_body="body" in settings.log.REQUEST_FIELDS,
            extract_client="client" in settings.log.REQUEST_FIELDS,
            extract_content_type="content_type" in settings.log.REQUEST_FIELDS,
            extract_cookies="cookies" in settings.log.REQUEST_FIELDS,
            extract_headers="headers" in settings.log.REQUEST_FIELDS,
            extract_method="method" in settings.log.REQUEST_FIELDS,
            extract_path="path" in settings.log.REQUEST_FIELDS,
            extract_path_params="path_params" in settings.log.REQUEST_FIELDS,
            extract_query="query" in settings.log.REQUEST_FIELDS,
            extract_scheme="scheme" in settings.log.REQUEST_FIELDS,
            obfuscate_cookies=settings.log.OBFUSCATE_COOKIES,
            obfuscate_headers=settings.log.OBFUSCATE_HEADERS,
            parse_body=True,
            parse_query=True,
        )
        self.response_extractor = ResponseDataExtractor(
            extract_body="body" in settings.log.RESPONSE_FIELDS,
            extract_headers="headers" in settings.log.RESPONSE_FIELDS,
            extract_status_code="status_code" in settings.log.RESPONSE_FIELDS,
            obfuscate_cookies=settings.log.OBFUSCATE_COOKIES,
            obfuscate_headers=settings.log.OBFUSCATE_HEADERS,
        )

    async def __call__(self, message: Message, _: State, scope: Scope) -> None:
        """Receives ASGI response messages and scope, and logs per
        configuration.

        Args:
            message: ASGI response event.
            scope: ASGI connection scope.
        """
        if scope["type"] == ScopeType.HTTP and self.exclude_paths.findall(scope["path"]):
            return

        if message["type"] == "http.response.start":
            scope["state"]["log_level"] = (
                logging.ERROR if message["status"] >= 500 else logging.INFO
            )
            scope["state"]["http.response.start"] = message
        # ignore intermediate content of streaming responses for now.
        elif message["type"] == "http.response.body" and message["more_body"] is False:
            scope["state"]["http.response.body"] = message
            if self.do_log_request:
                await self.log_request(scope)
            if self.do_log_response:
                await self.log_response(scope)
            await LOGGER.alog(scope["state"]["log_level"], settings.log.HTTP_EVENT)

    async def log_request(self, scope: "Scope") -> None:
        """Handles extracting the request data and logging the message.

        Args:
            scope: The ASGI connection scope.
        Returns:
            None
        """
        extracted_data = await self.extract_request_data(request=scope["app"].request_class(scope))
        structlog.contextvars.bind_contextvars(request=extracted_data)

    async def log_response(self, scope: "Scope") -> None:
        """Handles extracting the response data and logging the message.

        Args:
            scope: The ASGI connection scope.
        Returns:
            None
        """
        extracted_data = self.extract_response_data(scope=scope)
        structlog.contextvars.bind_contextvars(response=extracted_data)

    async def extract_request_data(self, request: Request) -> dict[str, Any]:
        """Creates a dictionary of values for the log.

        Args:
            request: A [Request][starlite.connection.request.Request] instance.
        Returns:
            An OrderedDict.
        """
        data: dict[str, Any] = {}
        extracted_data = self.request_extractor(connection=request)
        missing = object()
        for key in settings.log.REQUEST_FIELDS:
            value = extracted_data.get(key, missing)
            if value is missing:  # pragma: no cover
                continue
            if isawaitable(value):
                value = await value
            data[key] = value
        return data

    def extract_response_data(self, scope: Scope) -> dict[str, Any]:
        """Extracts data from the response.

        Args:
            scope: The ASGI connection scope.
        Returns:
            An OrderedDict.
        """
        data: dict[str, Any] = {}
        extracted_data = self.response_extractor(
            messages=(
                scope["state"]["http.response.start"],
                scope["state"]["http.response.body"],
            )
        )
        missing = object()
        for key in settings.log.RESPONSE_FIELDS:
            # https://github.com/starlite-api/starlite/issues/740
            value = extracted_data.get(key, missing)
            if value is missing:  # pragma: no cover
                continue
            data[key] = value
        return data
