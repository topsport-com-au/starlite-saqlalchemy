import logging

from starlette.responses import Response
from starlette.status import HTTP_409_CONFLICT
from starlite.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
)
from starlite.exceptions.utils import create_exception_response
from starlite.types import Request

__all__ = [
    "HTTPConflictException",
    "HTTPExceptionMixin",
    "HTTPInternalServerException",
    "HTTPNotFoundException",
    "logging_exception_handler",
]

logger = logging.getLogger(__name__)


class HTTPInternalServerException(InternalServerException):
    """
    Intended for use by repository objects in HTTP server context.
    """


class HTTPConflictException(HTTPException):
    """
    Intended for use by repository objects in HTTP server context.
    """

    status_code = HTTP_409_CONFLICT


class HTTPNotFoundException(NotFoundException):
    """
    Intended for use by repository objects in HTTP server context.
    """


def logging_exception_handler(_: Request, exc: Exception) -> Response:
    """
    Logs exception and returns appropriate response.

    Parameters
    ----------
    _ : Request
        The request that caused the exception.
    exc :
        The exception caught by the Starlite exception handling middleware and passed to the
        callback.

    Returns
    -------
    Response
    """
    logger.error("Application Exception", exc_info=exc)
    return create_exception_response(exc)


class HTTPExceptionMixin:
    """
    Mixin class for configuring repository objects to raise errors that return an HTTP response.

    Ensure to mixin such that this overwrites the class attributes on
    [`repository.Base`][starlite_lib.repository.Base]:

    ```python
    from starlite_lib import repository

    class Repo(HTTPExceptionMixin, repository.Base):
        ...
    ```
    """

    base_error_type: type[Exception] = HTTPInternalServerException
    integrity_error_type: type[Exception] = HTTPConflictException
    not_found_error_type: type[Exception] = HTTPNotFoundException
