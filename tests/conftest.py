"""Config that can be shared between all test types."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

import pytest
from starlite import Starlite
from structlog.contextvars import clear_contextvars
from structlog.testing import CapturingLogger

import starlite_saqlalchemy
from starlite_saqlalchemy import ConfigureApp, log


@pytest.fixture(name="cap_logger")
def fx_capturing_logger() -> CapturingLogger:
    """Used to monkeypatch the app logger, so we can inspect output."""
    return CapturingLogger()


@pytest.fixture(autouse=True)
def _patch_logger(cap_logger: CapturingLogger, monkeypatch: pytest.MonkeyPatch) -> None:
    starlite_saqlalchemy.log.configure(
        starlite_saqlalchemy.log.default_processors  # type:ignore[arg-type]
    )
    # clear context for every test
    clear_contextvars()
    # pylint: disable=protected-access
    logger = starlite_saqlalchemy.log.controller.LOGGER.bind()
    logger._logger = cap_logger
    # drop rendering processor to get a dict, not bytes
    # noinspection PyProtectedMember
    logger._processors = log.default_processors[:-1]
    monkeypatch.setattr(starlite_saqlalchemy.log.controller, "LOGGER", logger)
    monkeypatch.setattr(starlite_saqlalchemy.log.worker, "LOGGER", logger)


@pytest.fixture()
def app() -> Starlite:
    """Always use this `app` fixture and never do `from app.main import app`
    inside a test module. We need to delay import of the `app.main` module
    until as late as possible to ensure we can mock everything necessary before
    the application instance is constructed.

    Returns:
        The application instance.
    """
    return Starlite(route_handlers=[], on_app_init=[ConfigureApp()])


@pytest.fixture()
def raw_authors() -> list[dict[str, Any]]:
    """

    Returns:
        Raw set of author data that can either be inserted into tables for integration tests, or
        used to create `Author` instances for unit tests.
    """
    return [
        {
            "id": UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"),
            "name": "Agatha Christie",
            "dob": date(1890, 9, 15),
            "created": datetime.min,
            "updated": datetime.min,
        },
        {
            "id": UUID("5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"),
            "name": "Leo Tolstoy",
            "dob": date(1828, 9, 9),
            "created": datetime.min,
            "updated": datetime.min,
        },
    ]
