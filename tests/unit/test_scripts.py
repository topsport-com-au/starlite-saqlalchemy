"""Tests for scripts.py."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from starlite_saqlalchemy import scripts, settings
from starlite_saqlalchemy.testing import modify_settings

if TYPE_CHECKING:
    from pytest import MonkeyPatch


@pytest.mark.parametrize(("reload", "expected"), [(None, True), (True, True), (False, False)])
def test_uvicorn_config_auto_reload_local(
    reload: bool | None, expected: bool, monkeypatch: MonkeyPatch
) -> None:
    """Test that setting ENVIRONMENT to 'local' triggers auto reload."""
    monkeypatch.setattr(scripts, "IS_LOCAL_ENVIRONMENT", True)
    with modify_settings((settings.server, {"RELOAD": reload})):
        assert scripts.determine_should_reload() is expected


@pytest.mark.parametrize("reload", [True, False])
def test_uvicorn_config_reload_dirs(reload: bool) -> None:
    """Test that RELOAD_DIRS is only used when RELOAD is enabled."""
    if not reload:
        assert scripts.determine_reload_dirs(reload) is None
    else:
        reload_dirs = scripts.determine_reload_dirs(reload)
        assert reload_dirs is not None
        assert reload_dirs == settings.server.RELOAD_DIRS
