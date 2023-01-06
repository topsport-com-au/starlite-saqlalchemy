"""Tests for exception translation behavior."""
from unittest.mock import ANY, MagicMock

import pytest
from starlite import Starlite, get
from starlite.exceptions import ValidationException
from starlite.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from starlite.testing import RequestFactory, create_test_client

from starlite_saqlalchemy import exceptions
from starlite_saqlalchemy.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    StarliteSaqlalchemyError,
)


def test_after_exception_hook_handler_called(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that the handler gets added to the app and called."""
    logger_mock = MagicMock()
    monkeypatch.setattr(exceptions, "bind_contextvars", logger_mock)
    exc = RuntimeError()

    @get("/error")
    def raises() -> None:
        raise exc

    with create_test_client(
        route_handlers=[raises], after_exception=exceptions.after_exception_hook_handler
    ) as client:
        resp = client.get("/error")
        assert resp.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    logger_mock.assert_called_once_with(exc_info=(RuntimeError, exc, ANY))


def test_after_exception_hook_handler_doesnt_log_400(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that the handler doesn't call the logger if 400 exception."""
    logger_mock = MagicMock()
    monkeypatch.setattr(exceptions, "bind_contextvars", logger_mock)
    exc = ValidationException()

    @get("/error")
    def raises() -> None:
        raise exc

    with create_test_client(
        route_handlers=[raises], after_exception=exceptions.after_exception_hook_handler
    ) as client:
        resp = client.get("/error")
        assert resp.status_code == HTTP_400_BAD_REQUEST

    logger_mock.assert_not_called()


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (AuthorizationError, HTTP_403_FORBIDDEN),
        (ConflictError, HTTP_409_CONFLICT),
        (NotFoundError, HTTP_404_NOT_FOUND),
        (StarliteSaqlalchemyError, HTTP_500_INTERNAL_SERVER_ERROR),
    ],
)
def test_exception_to_http_response(exc: type[StarliteSaqlalchemyError], status: int) -> None:
    """Test translation of repository exceptions to Starlite HTTP exception
    types."""
    app = Starlite(route_handlers=[])
    request = RequestFactory(app=app, server="testserver").get("/wherever")
    response = exceptions.starlite_saqlalchemy_exception_to_http_response(request, exc())
    assert response.status_code == status


def test_exception_serves_debug_middleware_response() -> None:
    """Test behavior of exception translation in debug mode."""
    app = Starlite(route_handlers=[], debug=True)
    request = RequestFactory(app=app, server="testserver").get("/wherever")
    response = exceptions.starlite_saqlalchemy_exception_to_http_response(
        request, StarliteSaqlalchemyError("message")
    )
    assert response.body == b"starlite_saqlalchemy.exceptions.StarliteSaqlalchemyError: message\n"
