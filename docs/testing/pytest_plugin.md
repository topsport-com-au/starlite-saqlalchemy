# Pytest Plugin

The nature of applications built with the `starlite-saqlalchemy` pattern is that they rely heavily
on connected services.

Abstraction of [PostgreSQL][2] and [Redis][3] connectivity boilerplate is a nice convenience,
however to successfully patch the application for testing requires deeper knowledge of the
implementation than would be otherwise necessary.

So, `starlite-saqlalchemy` ships with a selection of [pytest fixtures][1] that are often necessary
when building applications such as these.

## `app`

The `app` fixture provides an instance of a `Starlite` application.

```python
from __future__ import annotations

from starlite import Starlite


def test_app_fixture(app: Starlite) -> None:
    assert isinstance(app, Starlite)
```

The value of Pytest ini option, `test_app` is used to determine the application to load.

```toml
# pyproject.toml

[tool.pytest.ini_options]
test_app = "app.main:create_app"
```

If no value is configured for the `test_app` ini option, the default location of
`"app.main:create_app"` is searched.

The value of the `test_app` ini option can either point to an application factory or `Starlite`
instance.

If the object found at the import path is not a `Starlite` instance, the fixture assumes it is
an application factory, and will call the object and return the response.

The value of `test_app` is resolved using the uvicorn `import_from_string()` function, so it
supports the same format as `uvicorn` supports for its `app` and `factory` parameters.

## `client`

A `starlite.testing.TestClient` instance, wired to the same application that is produced by the
`app` fixture.

## `cap_logger`

The `cap_logger` fixture provides an instance of [`structlog.testing.CapturingLogger`][4].

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from structlog.testing import CapturedCall

if TYPE_CHECKING:
    from structlog.testing import CapturingLogger


def test_app_fixture(cap_logger: CapturingLogger) -> None:
    cap_logger.info("hello")
    cap_logger.info("hello", when="again")
    assert cap_logger.calls == [
        CapturedCall(method_name="info", args=("hello",), kwargs={}),
        CapturedCall(method_name="info", args=("hello",), kwargs={"when": "again"}),
    ]
```

The `cap_logger` fixture will capture any `structlog` calls made by the starlite application or the
SAQ worker, so that they can be inspected as part of tests.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import AsyncClient

if TYPE_CHECKING:
    from starlite import Starlite
    from structlog.testing import CapturingLogger


async def test_health_logging_skipped(
    app: Starlite, cap_logger: CapturingLogger
) -> None:
    """Test that calls to the health check route are not logged."""

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200

    assert [] == cap_logger.calls
```

## is_unit_test

The `is_unit_test` fixture returns a `bool` that indicates if the test suite believes it is running
a unit test, or an integration test.

To determine this, we compare the path of the running test to the value of the Pytest ini option
`unit_test_pattern`, which by default is `"^.*/tests/unit/.*$"`.

This fixture is used to make fixtures behave differently between unit and integration test contexts.

## _patch_http_close

This is an [`autouse` fixture][5], that prevents HTTP clients that are defined in the global scope
from being closed.

The application is configured to close all instantiated HTTP clients on app shutdown, however when
apps are defined in a global/class scope, a test that runs after the first application shutdown in
the test suite would fail.

## _patch_sqlalchemy_plugin

This is an [`autouse` fixture][5], that mocks out the `on_shutdown` method of the SQLAlchemy config
object for unit tests.

## _patch_worker

This is an [`autouse` fixture][5], that mocks out the `on_app_startup` and `stop` methods of
`worker.Worker` type for unit tests.

[1]: https://docs.pytest.org/en/latest/explanation/fixtures.html#about-fixtures
[2]: https://www.postgresql.org/
[3]: https://redis.io
[4]: https://www.structlog.org/en/stable/api.html#structlog.testing.CapturingLogger
[5]: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
