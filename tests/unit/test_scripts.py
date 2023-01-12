"""Tests for scripts.py."""

import pytest

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.scripts import determine_reload_dirs, determine_should_reload
from starlite_saqlalchemy.testing import modify_settings


@pytest.mark.parametrize(("reload", "expected"), [(None, True), (True, True), (False, False)])
def test_uvicorn_config_auto_reload_local(reload: bool | None, expected: bool) -> None:
    """Test that setting ENVIRONMENT to 'local' triggers auto reload."""
    with modify_settings(
        (settings.app, {"ENVIRONMENT": "local"}), (settings.server, {"RELOAD": reload})
    ):
        assert determine_should_reload() is expected


@pytest.mark.parametrize("reload", [True, False])
def test_uvicorn_config_reload_dirs(reload: bool) -> None:
    """Test that RELOAD_DIRS is only used when RELOAD is enabled."""
    if not reload:
        assert determine_reload_dirs(reload) is None
    else:
        reload_dirs = determine_reload_dirs(reload)
        assert reload_dirs is not None
        assert reload_dirs == settings.server.RELOAD_DIRS
