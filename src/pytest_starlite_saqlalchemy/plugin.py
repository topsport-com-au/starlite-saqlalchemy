"""Pytest plugin to support testing starlite-saqlalchemy applications."""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from starlite import Starlite, TestClient
from structlog.contextvars import clear_contextvars
from structlog.testing import CapturingLogger
from uvicorn.importer import ImportFromStringError, import_from_string

from starlite_saqlalchemy import constants

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest import Config, FixtureRequest, MonkeyPatch, Parser

__all__ = (
    "_patch_http_close",
    "_patch_sqlalchemy_plugin",
    "_patch_worker",
    "fx_app",
    "fx_cap_logger",
    "fx_client",
    "fx_is_unit_test",
    "pytest_addoption",
)


def pytest_addoption(parser: Parser) -> None:
    """Adds Pytest ini config variables for the plugin."""
    parser.addini(
        "test_app",
        "Path to application instance, or callable that returns an application instance.",
        type="string",
        default=os.environ.get("TEST_APP", "app.main:create_app"),
    )
    parser.addini(
        "unit_test_pattern",
        (
            "Regex used to identify if a test is running as part of a unit or integration test "
            "suite. The pattern is matched against the path of each test function and affects the "
            "behavior of fixtures that are shared between unit and integration tests."
        ),
        type="string",
        default=r"^.*/tests/unit/.*$",
    )


@pytest.fixture(name="is_unit_test")
def fx_is_unit_test(request: FixtureRequest) -> bool:
    """Uses the ini option `unit_test_pattern` to determine if the test is part
    of unit or integration tests."""
    unittest_pattern: str = request.config.getini("unit_test_pattern")  # pyright:ignore
    return bool(re.search(unittest_pattern, str(request.path)))


@pytest.fixture(autouse=True)
def _patch_http_close(monkeypatch: MonkeyPatch) -> None:
    """We don't want global http clients to get closed between tests."""
    import starlite_saqlalchemy

    monkeypatch.setattr(starlite_saqlalchemy.http, "clients", set())


@pytest.fixture(autouse=constants.IS_SQLALCHEMY_INSTALLED)
def _patch_sqlalchemy_plugin(is_unit_test: bool, monkeypatch: MonkeyPatch) -> None:
    if is_unit_test:
        from starlite_saqlalchemy import sqlalchemy_plugin

        monkeypatch.setattr(
            sqlalchemy_plugin.SQLAlchemyConfig,  # type:ignore[attr-defined]
            "on_shutdown",
            MagicMock(),
        )


@pytest.fixture(autouse=constants.IS_SAQ_INSTALLED)
def _patch_worker(is_unit_test: bool, monkeypatch: MonkeyPatch) -> None:
    """We don't want the worker to start for unittests."""
    if is_unit_test:
        from starlite_saqlalchemy import worker

        monkeypatch.setattr(worker.Worker, "on_app_startup", MagicMock())
        monkeypatch.setattr(worker.Worker, "stop", MagicMock())


@pytest.fixture(name="app")
def fx_app(pytestconfig: Config, monkeypatch: MonkeyPatch) -> Starlite:
    """
    Returns:
        An application instance, configured via plugin.
    """
    test_app_str = pytestconfig.getini("test_app")
    try:
        app_or_callable = import_from_string(test_app_str)
    except (ImportFromStringError, ModuleNotFoundError):
        from starlite_saqlalchemy.init_plugin import ConfigureApp

        app = Starlite(route_handlers=[], on_app_init=[ConfigureApp()], openapi_config=None)
    else:
        if isinstance(app_or_callable, Starlite):
            app = app_or_callable
        else:
            app = app_or_callable()

    monkeypatch.setattr(app, "before_startup", [])
    return app


@pytest.fixture(name="client")
def fx_client(app: Starlite) -> Generator[TestClient, None, None]:
    """Test client fixture for making calls on the global app instance."""
    with TestClient(app=app) as client:
        yield client


@pytest.fixture(name="cap_logger")
def fx_cap_logger(monkeypatch: MonkeyPatch) -> CapturingLogger:
    """Used to monkeypatch the app logger, so we can inspect output."""
    import starlite_saqlalchemy

    starlite_saqlalchemy.log.configure(
        starlite_saqlalchemy.log.default_processors  # type:ignore[arg-type]
    )
    # clear context for every test
    clear_contextvars()
    # pylint: disable=protected-access
    logger = starlite_saqlalchemy.log.controller.LOGGER.bind()
    logger._logger = CapturingLogger()
    # drop rendering processor to get a dict, not bytes
    # noinspection PyProtectedMember
    logger._processors = starlite_saqlalchemy.log.default_processors[:-1]
    monkeypatch.setattr(starlite_saqlalchemy.log.controller, "LOGGER", logger)
    monkeypatch.setattr(starlite_saqlalchemy.log.worker, "LOGGER", logger)
    return logger._logger
