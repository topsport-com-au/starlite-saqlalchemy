"""Test application."""
from __future__ import annotations

from starlite import Starlite

from starlite_saqlalchemy import ConfigureApp

from . import controllers


def create_app() -> Starlite:
    """App for our test domain."""
    return Starlite(route_handlers=[controllers.create_router()], on_app_init=[ConfigureApp()])
