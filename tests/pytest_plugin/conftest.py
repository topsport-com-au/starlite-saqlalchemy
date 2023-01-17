"""Enable the `pytester` fixture for the plugin tests."""
from __future__ import annotations

from importlib import reload

import pytest

from starlite_saqlalchemy.db import orm

pytest_plugins = ["pytester"]


@pytest.fixture(autouse=True)
def _reload_orm() -> None:
    reload(orm)
