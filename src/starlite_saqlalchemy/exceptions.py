"""Definition of extra HTTP exceptions that aren't included in `Starlite`.

Also, defines functions that translate service and repository exceptions
into HTTP exceptions.
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from starlite.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
)
from starlite.middleware.exceptions.debug_response import create_debug_response
from starlite.utils.exception import create_exception_response
from structlog.contextvars import bind_contextvars

if TYPE_CHECKING:
    from typing import Any

    from starlite.connection import Request
    from starlite.datastructures import State
    from starlite.response import Response
    from starlite.types import Scope
    from starlite.utils.exception import ExceptionResponseContent

__all__ = (
    "AuthorizationError",
    "ConflictError",
    "NotFoundError",
    "StarliteSaqlalchemyError",
    "after_exception_hook_handler",
)


class StarliteSaqlalchemyError(Exception):
    """Base exception type for the lib's custom exception types."""


class ConflictError(StarliteSaqlalchemyError):
    """Exception for data integrity errors."""


class NotFoundError(StarliteSaqlalchemyError):
    """Referenced identity doesn't exist."""


class AuthorizationError(StarliteSaqlalchemyError):
    """A user tried to do something they shouldn't have."""


class _HTTPConflictException(HTTPException):
    """Request conflict with the current state of the target resource."""

    status_code = 409


class _HTTPForbiddenException(HTTPException):
    """Server understands the request but refuses to authorize it."""

    status_code = 403


async def after_exception_hook_handler(exc: Exception, _scope: Scope, _state: State) -> None:
    """Binds `exc_info` key with exception instance as value to structlog
    context vars.

    This must be a coroutine so that it is not wrapped in a thread where we'll lose context.

    Args:
        exc: the exception that was raised.
        _scope: scope of the request
        _state: application state
    """
    if isinstance(exc, HTTPException) and exc.status_code < 500:
        return
    bind_contextvars(exc_info=sys.exc_info())


def starlite_saqlalchemy_exception_to_http_response(
    request: Request[Any, Any], exc: StarliteSaqlalchemyError
) -> Response[ExceptionResponseContent]:
    """Transform repository exceptions to HTTP exceptions.

    Args:
        request: The request that experienced the exception.
        exc: Exception raised during handling of the request.

    Returns:
        Exception response appropriate to the type of original exception.
    """
    http_exc: type[HTTPException]
    if isinstance(exc, NotFoundError):
        http_exc = NotFoundException
    elif isinstance(exc, ConflictError):
        http_exc = _HTTPConflictException
    elif isinstance(exc, AuthorizationError):
        http_exc = _HTTPForbiddenException
    else:
        http_exc = InternalServerException
    if http_exc is InternalServerException and request.app.debug:
        return create_debug_response(request, exc)
    return create_exception_response(http_exc())
