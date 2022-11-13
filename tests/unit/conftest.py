"""Unit test specific config."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from saq.job import Job  # type:ignore[import]
from starlite.datastructures import State
from starlite.enums import ScopeType
from starlite.testing import TestClient

from starlite_saqlalchemy import sqlalchemy_plugin, worker
from starlite_saqlalchemy.testing import GenericMockRepository

from ..utils import controllers, domain

if TYPE_CHECKING:
    from collections import abc
    from uuid import UUID

    from starlite import Starlite
    from starlite.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope


@pytest.fixture(scope="session", autouse=True)
def _patch_sqlalchemy_plugin() -> abc.Iterator:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        sqlalchemy_plugin.SQLAlchemyConfig,  # type:ignore[attr-defined]
        "on_shutdown",
        MagicMock(),
    )
    yield
    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def _patch_worker() -> abc.Iterator:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(worker.Worker, "on_app_startup", MagicMock())
    monkeypatch.setattr(worker.Worker, "stop", MagicMock())
    yield
    monkeypatch.undo()


@pytest.fixture(autouse=True)
def _author_repository(raw_authors: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    AuthorRepository = GenericMockRepository[domain.Author]
    collection: dict[UUID, domain.Author] = {}
    for raw_author in raw_authors:
        author = domain.Author(**raw_author)
        collection[getattr(author, AuthorRepository.id_attribute)] = author
    monkeypatch.setattr(AuthorRepository, "collection", collection)
    monkeypatch.setattr(domain, "Repository", AuthorRepository)
    monkeypatch.setattr(domain.Service, "repository_type", AuthorRepository)


@pytest.fixture()
def client(app: Starlite) -> abc.Iterator[TestClient]:
    """Client instance attached to app.

    Args:
        app: The app for testing.

    Returns:
        Test client instance.
    """
    with TestClient(app=app) as client_:
        yield client_


@pytest.fixture()
def http_response_start() -> HTTPResponseStartEvent:
    """ASGI message for start of response."""
    return {"type": "http.response.start", "status": 200, "headers": []}


@pytest.fixture()
def http_response_body() -> HTTPResponseBodyEvent:
    """ASGI message for interim, and final response body messages.

    Note:
        `more_body` is `True` for interim body messages.
    """
    return {"type": "http.response.body", "body": b"body", "more_body": False}


@pytest.fixture()
def http_scope(app: Starlite) -> HTTPScope:
    """Minimal ASGI HTTP connection scope."""
    return {
        "headers": [],
        "app": app,
        "asgi": {"spec_version": "whatever", "version": "3.0"},
        "auth": None,
        "client": None,
        "extensions": None,
        "http_version": "3",
        "path": "/wherever",
        "path_params": {},
        "query_string": b"",
        "raw_path": b"/wherever",
        "root_path": "/",
        "route_handler": controllers.get_author,
        "scheme": "http",
        "server": None,
        "session": {},
        "state": {},
        "user": None,
        "method": "GET",
        "type": ScopeType.HTTP,
    }


@pytest.fixture()
def state() -> State:
    """Starlite application state datastructure."""
    return State()


@pytest.fixture()
def job() -> Job:
    """SAQ Job instance."""
    return Job(function="whatever", kwargs={"a": "b"})
