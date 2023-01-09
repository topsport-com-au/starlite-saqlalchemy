from pathlib import Path

import pytest

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.scripts import _get_uvicorn_config
from starlite_saqlalchemy.testing import modify_settings


@pytest.mark.parametrize(("reload", "expected"), [(None, True), (True, True), (False, False)])
def test_uvicorn_config_auto_reload_local(reload, expected):
    with modify_settings(
        (settings.app, {"ENVIRONMENT": "local"}), (settings.server, {"RELOAD": reload})
    ):
        config = _get_uvicorn_config()
        assert config.reload is expected


@pytest.mark.parametrize(
    ("reload", "expected"), [(None, []), (True, settings.server.RELOAD_DIRS), (False, [])]
)
def test_uvicorn_config_reload_dirs(reload, expected):
    with modify_settings((settings.server, {"RELOAD": reload})):
        config = _get_uvicorn_config()
        assert config.reload_dirs == [Path(path).absolute() for path in expected]
