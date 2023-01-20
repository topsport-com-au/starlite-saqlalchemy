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
from .init_plugin import ConfigureApp, PluginConfig

__all__ = [
    "ConfigureApp",
    "PluginConfig",
    "compression",
    "dependencies",
    "exceptions",
    "health",
    "http",
    "log",
    "openapi",
    "repository",
    "service",
    "settings",
    "type_encoders",
]


__version__ = "0.29.0"
