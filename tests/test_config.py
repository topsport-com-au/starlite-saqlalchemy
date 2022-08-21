from typing import Any

from starlite_lib.config import DatabaseSettings


def test_db_settings_echo_pool_true(monkeypatch: Any) -> None:
    monkeypatch.setenv("DB_ECHO_POOL", "true")
    assert DatabaseSettings().ECHO_POOL is True


def test_db_settings_echo_pool_false(monkeypatch: Any) -> None:
    monkeypatch.setenv("DB_ECHO_POOL", "false")
    assert DatabaseSettings().ECHO_POOL is False


def test_db_settings_echo_pool_debug(monkeypatch: Any) -> None:
    monkeypatch.setenv("DB_ECHO_POOL", "debug")
    assert DatabaseSettings().ECHO_POOL == "debug"
