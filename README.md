<h1 align="center">starlite-saqlalchemy</h1>
<p align="center">
  <img src="https://www.topsport.com.au/assets/images/logo_pulse.svg" width="200" alt="TopSport Pulse"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/starlite-saqlalchemy">
    <img src="https://img.shields.io/pypi/v/starlite-saqlalchemy" alt="PYPI: starlite-saqlalchemy"/>
  </a>
  <a href="https://github.com/topsport-com-au/starlite-saqlalchemy/blob/main/LICENSE">
    <img src="https://img.shields.io/pypi/l/starlite-saqlalchemy?color=blue" alt="License: MIT"/>
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/pypi/pyversions/starlite-saqlalchemy" alt="Python: supported versions"/>
  </a>
  <a href="https://results.pre-commit.ci/latest/github/topsport-com-au/starlite-saqlalchemy/main">
    <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/topsport-com-au/starlite-saqlalchemy/main.svg"/>
  </a>
  <a href="https://bestpractices.coreinfrastructure.org/projects/6646">
    <img alt="OpenSSF Best Practices" src="https://bestpractices.coreinfrastructure.org/projects/6646/badge">
  </a>
  <a href="https://github.com/topsport-com-au/starlite-saqlalchemy/actions/workflows/ci.yml">
    <img alt="Actions: CI" src="https://github.com/topsport-com-au/starlite-saqlalchemy/actions/workflows/ci.yml/badge.svg?branch=main&event=push"/>
  </a>
</p>
<p align="center">
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Reliability Rating" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=reliability_rating"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=alert_status"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=coverage"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=sqale_rating"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=security_rating"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=bugs"/>
  </a>
  <a href="https://sonarcloud.io/summary/new_code?id=topsport-com-au_starlite-saqlalchemy">
    <img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=topsport-com-au_starlite-saqlalchemy&metric=vulnerabilities"/>
  </a>
</p>

Configuration for a [Starlite](https://github.com/starlite-api/starlite) application that features:

- SQLAlchemy 2.0
- SAQ async worker
- Lots of features!

## Example

```python
from starlite import Starlite, get

from starlite_saqlalchemy import ConfigureApp


@get("/example")
def example_handler() -> dict:
    """Hello, world!"""
    return {"hello": "world"}


app = Starlite(route_handlers=[example_handler], on_app_init=[ConfigureApp()])
```

## Features

The application configured in the above example includes the following configuration.

### Logging after exception handler

Receives and logs any unhandled exceptions raised out of route handling.

### Redis cache

Integrates a Redis cache backend with Starlite first-class cache support.

### Collection route filters

Support filtering collection routes by created and updated timestamps, list of ids, and limit/offset
pagination.

Includes an aggregate `filters` dependency to easily inject all filters into a route handler, e.g,:

```python
from starlite import get
from starlite_saqlalchemy.dependencies import FilterTypes


@get()
async def get_collection(filters: list[FilterTypes]) -> list[...]:
    ...
```

### Gzip compression

Configures Starlite's built-in Gzip compression support.

### Exception handlers

Exception handlers that translate non-Starlite repository and service object exception
types into Starlite's HTTP exceptions.

### Health check

A health check route handler that returns some basic application info.

### Logging

Configures logging for the application including:

- Queue listener handler, appropriate for asyncio applications
- Health check route filter so that health check requests don't clog your logs
- An informative log format
- Configuration for dependency logs

### Openapi config

Configures OpenAPI docs for the application, including config by environment to allow for easy
personalization per application.

### Starlite Response class

A response class that can handle serialization of SQLAlchemy/Postgres UUID types.

### Sentry configuration

Just supply the DSN via environment, and Sentry is configured for you.

### SQLAlchemy

Engine, logging, pooling etc all configurable via environment. We configure starlite and include a
custom `before_send` wrapper that inspects the outgoing status code to determine whether the
transaction that represents the request should be committed, or rolled back.

### Async SAQ worker config

A customized SAQ queue and worker that is started and shutdown using the Starlite lifecycle event
hooks - no need to run your worker in another process, we attach it to the same event loop as the
Starlite app uses. Be careful not to do things in workers that will block the loop!

## Extra Features

In addition to application config, the library include:

### Repository

An abstract repository object type and a SQLAlchemy repository implementation.

### DTO Factory

A factory for building pydantic models from SQLAlchemy 2.0 style declarative classes. Use these to
annotate the `data` parameter and return type of routes to control the data that can be modified per
route, and the information included in route responses.

### HTTP Client and Endpoint decorator

`http.Client` is a wrapper around `httpx.AsyncClient` with some extra features including unwrapping
enveloped data, and closing the underlying client during shutdown of the Starlite application.

### ORM Configuration

A SQLAlchemy declarative base class that includes:

- a mapping of the builtin `UUID` type to the postgresql dialect UUID type.
- an `id` column
- a `created` timestamp column
- an `updated` timestamp column
- an automated `__tablename__` attribute
- a `from_dto()` class method, to ease construction of model types from DTO objects.

We also add:

- a `before_flush` event listener that ensures that the `updated` timestamp is touched on instances
  on their way into the database.
- a constraint naming convention so that index and constraint names are automatically generated.

### Service object

A Service object that integrates with the Repository ABC and provides standard logic for typical
operations.

### Settings

Configuration by environment.

## Contributing

All contributions big or small are welcome and appreciated! Please check out `CONTRIBUTING.md` for
specific information about configuring your environment and workflows used by this project.
