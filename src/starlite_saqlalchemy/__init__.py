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
    compression,
    dependencies,
    exceptions,
    health,
    http,
    log,
    openapi,
    repository,
    service,
    settings,
    type_encoders,
)
from .constants import (
    IS_REDIS_INSTALLED,
    IS_SAQ_INSTALLED,
    IS_SENTRY_SDK_INSTALLED,
    IS_SQLALCHEMY_INSTALLED,
)
from .init_plugin import ConfigureApp, PluginConfig

if IS_SENTRY_SDK_INSTALLED:
    from . import sentry

if IS_SAQ_INSTALLED:
    from . import worker

if IS_REDIS_INSTALLED:
    from . import cache, redis

if IS_SQLALCHEMY_INSTALLED:
    from . import db, dto, sqlalchemy_plugin


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
    "http",
    "log",
    "openapi",
    "redis",
    "repository",
    "sentry",
    "service",
    "settings",
    "sqlalchemy_plugin",
    "type_encoders",
    "worker",
]


__version__ = "0.28.1"
