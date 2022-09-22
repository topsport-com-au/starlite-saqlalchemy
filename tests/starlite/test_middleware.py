from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from starlite_lib.init_plugin import db, get

from ..utils import make_test_client_request

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_session_commit_called_after_success(monkeypatch: "MonkeyPatch") -> None:
    @get("/")
    def handler() -> None:
        pass

    session_mock = AsyncMock()
    monkeypatch.setattr(db, "AsyncScopedSession", session_mock)
    r = make_test_client_request([handler], "/")
    assert r.status_code == 200
    session_mock.commit.assert_called_once()
    session_mock.remove.assert_called_once()


def test_session_rollback_called_after_error(monkeypatch: "MonkeyPatch") -> None:
    @get("/", status_code=500)
    def handler() -> None:
        pass

    session_mock = AsyncMock()
    monkeypatch.setattr(db, "AsyncScopedSession", session_mock)
    r = make_test_client_request([handler], "/")
    assert r.status_code == 500
    session_mock.rollback.assert_called_once()
    session_mock.remove.assert_called_once()


def test_session_rollback_called_after_exception(monkeypatch: "MonkeyPatch") -> None:
    @get("/")
    def handler() -> None:
        raise RuntimeError

    session_mock = AsyncMock()
    monkeypatch.setattr(db, "AsyncScopedSession", session_mock)
    r = make_test_client_request([handler], "/")
    assert r.status_code == 500
    session_mock.rollback.assert_called_once()
    session_mock.remove.assert_called_once()
