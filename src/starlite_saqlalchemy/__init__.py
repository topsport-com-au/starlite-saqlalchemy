"""
starlite-saqlalchemy
---

An implementation of a `Starlite` application configuration plugin.

Example:
```python
from starlite import Starlite, get

from starlite_saqlalchemy import ConfigureApp


@get("/example")
def example_handler() -> dict:
    return {"hello": "world"}


app = Starlite(route_handlers=[example_handler], on_app_init=[ConfigureApp()])
```
"""
# this is because pycharm wigs out when there is a module called `exceptions`:
# noinspection PyCompatibility
from . import (
    cache,
    compression,
    db,
    dependencies,
    dto,
    exceptions,
    health,
    log,
    openapi,
    redis,
    repository,
    sentry,
    service,
    settings,
    sqlalchemy_plugin,
    worker,
)
from .init_plugin import ConfigureApp, PluginConfig

__all__ = [
    "ConfigureApp",
    "PluginConfig",
    "cache",
    "compression",
    "db",
    "dependencies",
    "dto",
    "exceptions",
    "health",
    "log",
    "openapi",
    "redis",
    "repository",
    "sentry",
    "service",
    "settings",
    "sqlalchemy_plugin",
    "worker",
]

__version__ = "0.14.2"
