# starlite-saqlalchemy

An API application pattern standing on the shoulders of:

- [Starlite](https://starlite-api.github.io/starlite/): "...a light, opinionated and flexible ASGI
  API framework built on top of pydantic".
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/): "The Python SQL Toolkit and Object
  Relational Mapper".
- [SAQ](https://github.com/tobymao/saq): "...a simple and performant job queueing framework built on
  top of asyncio and redis".
- [Structlog](https://www.structlog.org/en/stable/): "...makes logging in Python faster, less
  painful, and more powerful".

## Usage Example

```py title="Simple Example"
--8<-- "examples/basic_example.py"
```

Check out the [Usage](config/) section to see everything that is enabled by the framework!

## Pattern

This is the pattern encouraged by this framework:

``` mermaid
sequenceDiagram
  Client ->> Controller: Inbound request data
  Controller ->> Service: Invoke service with data validated by DTO
  Service ->> Repository: View or modify the collection
  Repository ->> Service: Detached SQLAlchemy instance(s)
  Service ->> Queue: Optionally enqueue an async callback
  Service ->> Controller: Outbound data
  Controller ->> Client: Serialize via DTO
  Queue ->> Worker: Worker invoked
  Worker ->> Service: Makes async callback
```

- Request data is deserialized and validated by Starlite before it is received by controller.
- Controller invokes relevant service object method and waits for response.
- Service method handles business logic of the request and optionally triggers an asynchronous
  callback.
- Service method returns to controller and response is made to client.
- Async worker makes callback to service object where any async tasks can be performed.
  Depending on architecture, this may not be the same instance of the application that handled the
  request.

## Motivation

A modern, production-ready API application has a lot of components. Starlite, the backbone of this
library, exposes a plethora of features and functionality that requires some amount of boilerplate
and configuration that must be carried from one implementation of an application to
the next.

`starlite-saqlalchemy` is an example of how Starlite's `on_app_init` hook can be utilized to build
application configuration libraries that support streamlining the application development process.

However, this library intends to be not only an example, but also an opinionated resource to support
the efficient, and consistent rollout of production ready API applications built on top of Starlite.

Use this library if the stack and design decisions suit your taste. If there are improvements or
generalizations that could be made to the library to support your use case, we'd love to hear about
them. Open [an issue](https://github.com/topsport-com-au/starlite-saqlalchemy/issues) or start
[a discussion](https://github.com/topsport-com-au/starlite-saqlalchemy/discussions).

## Backward compatibility and releases

This project follows semantic versioning, and we use
[semantic releases](https://python-semantic-release.readthedocs.io/en/latest/) in our toolchain.
This means that bug fixes and new features will find there way into a release as soon they hit the
main branch, and if we break something, we'll bump the major version number. However, until we hit
v1.0, there will be breaking changes between minor versions, but v1.0 is close!
