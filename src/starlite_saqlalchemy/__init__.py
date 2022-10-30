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
    dependencies,
    dto,
    exceptions,
    health,
    logging,
    openapi,
    orm,
    redis,
    repository,
    response,
    sentry,
    service,
    settings,
    sqlalchemy_plugin,
    static_files,
    worker,
)
from .init_plugin import ConfigureApp, PluginConfig

__all__ = [
    "ConfigureApp",
    "PluginConfig",
    "cache",
    "compression",
    "dependencies",
    "dto",
    "exceptions",
    "health",
    "logging",
    "openapi",
    "orm",
    "redis",
    "repository",
    "response",
    "sentry",
    "service",
    "settings",
    "sqlalchemy_plugin",
    "static_files",
    "worker",
]

__version__ = "0.1.6"
