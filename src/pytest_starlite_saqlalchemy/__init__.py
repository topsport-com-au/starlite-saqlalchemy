"""Pytest plugin to support testing starlite-saqlalchemy applications."""
from __future__ import annotations

from .plugin import (
    _patch_http_close,
    _patch_sqlalchemy_plugin,
    _patch_worker,
    cap_logger,
    fx_app,
    fx_client,
    is_unit_test,
    pytest_addoption,
)
