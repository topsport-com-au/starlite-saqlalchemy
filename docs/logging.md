# Logging

`starlite-saqlalchemy` has structured logging baked-in, built around facilitating the
[Canonical Log Lines](https://brandur.org/canonical-log-lines) pattern (which is basically, a
single log line per request or async worker invocation).

The pattern is built upon the excellent [`structlog`](https://github.com/hynek/structlog) library,
and is configured to be as efficient as possible while not blocking the event loop (it runs the
logging in a processor thread).

## Adding data to the log

To bind a key/value pair to the log object _anywhere_ within the application, use
`structlog.contextvars.bind_contextvars`.

```python
from structlog.contextvars import bind_contextvars


def do_something() -> None:
    ...
    bind_contextvars(i_did="something")
```

Whether you call that in the context of handling an HTTP request, or during an async worker
invocation, it doesn't matter, that key/value pair will be included in the log representing that
invocation.

## Controller Logging

### Middleware

The configuration adds a very light-weight middleware that simply clears the context-local storage
for each request.

### Before Send Hook Handler

We add a handler to Starlite's
[`before_send`](https://starlite-api.github.io/starlite/usage/0-the-starlite-app/5-application-hooks/#before-send)
hook. That allows us to do two things:

1. We inspect the outbound messages looking for a
   [Response Start](https://asgi.readthedocs.io/en/latest/specs/www.html#response-start-send-event)
   event. When that is located, we stash the message into the connection scope state, for later use.
   We also use this event to determine the severity of the eventual log message. If the status code
   is in the 500s we log at ERROR, otherwise INFO.
2. We inspect the outbound messages looking for a
   [Response Body](https://asgi.readthedocs.io/en/latest/specs/www.html#response-body-send-event)
   event. This event has a property called `more_body`, for streaming responses this flag indicates
   whether there is another `Response Body` message to come. If `more_body` is `True` we do nothing,
   but once we receive the final `Response Body` message of the request we use it to construct the
   response log, and finally emit the log message at the predetermined severity level.

### Example

Here's an example of a log emitted with the default configuration (I've applied the formatting for
the purposes of this documentation, the logger emits un-formatted json):

```json
{
    "event": "HTTP",
    "level": "info",
    "request": {
        "body": {
            "dob": "1890-9-15",
            "name": "TEST UPDATE"
        },
        "content_type": [
            "application/json",
            {}
        ],
        "cookies": {},
        "headers": {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "connection": "keep-alive",
            "content-length": "43",
            "content-type": "application/json",
            "host": "testserver",
            "user-agent": "python-httpx/0.23.0"
        },
        "method": "PUT",
        "path": "/authors/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        "path_params": {
            "author_id": "97108ac1-ffcb-411d-8b1e-d9183399f63b"
        },
        "query": {}
    },
    "response": {
        "body": "b'{\"id\":\"97108ac1-ffcb-411d-8b1e-d9183399f63b\",\"created\":\"0001-01-01T00:00:00\",\"updated\":\"2022-11-04T14:15:16\",\"name\":\"TEST UPDATE\",\"dob\":\"1890-09-15\"}'",
        "cookies": {},
        "headers": {
            "content-length": "149",
            "content-type": "application/json"
        },
        "status_code": 200
    },
    "timestamp": "2022-11-04T04:15:16.766464Z"
}
```

### Controlling Log Content

As you can see, we are including a lot of data in our logs that may include sensitive values, such
as [PII](https://en.wikipedia.org/wiki/Personal_data) and secrets.

Thankfully, we have mechanisms to ensure that this type of data is excluded from our logs!

Our
[LogSettings](../reference/starlite_saqlalchemy/settings/#starlite_saqlalchemy.settings.LogSettings)
object provides a host of options that allow you to customize log output. This exposes the following
environment variables:

#### `LOG_EXCLUDE_PATHS`

This is a [regular expression](https://docs.python.org/3/library/re.html) that is matched against
the path of the request before logging. If the path matches the regex, the route is not logged.

For example, the value `^/a` will exclude any path that begins with `/a`, such as `/apath` and
`/a/path`.

Explicit paths can be excluded by using the "start" (`^`) and "end" (`$`) symbols, for example
`^/never-log$` will exclude the path `/never-log` but will not exclude `/never-log/just/joking`.

Multiple regexes can be concatenated with the "or" symbol (`|`).

#### LOG_OBFUSCATE_COOKIES & LOG_OBFUSCATE_HEADERS

These two environment variables allow you to specify header and cookie names, whose value will be
obfuscated in the logs.

This leverages functionality that is provided via Starlite's
[Extraction Utils](https://starlite-api.github.io/starlite/reference/utils/4-extractor-utils/).

Simply provide the exact name of the cookies and headers that should be obfuscated.

As environment variables are parsed by pydantic, collections such as these should be JSON strings
(per [their documentation](https://pydantic-docs.helpmanual.io/usage/settings/#parsing-environment-variable-values))
. For example:

```text
LOG_OBFUSCATE_HEADERS='["Authorization", "X-API-KEY"]'`
```

#### LOG_REQUEST_FIELDS & LOG_RESPONSE_FIELDS

These specify the fields from the
[ASGI Connection Scope](https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope)
and response messages that are included in logs.

As environment variables are parsed by pydantic, collections such as these should be JSON strings
(per [their documentation](https://pydantic-docs.helpmanual.io/usage/settings/#parsing-environment-variable-values))
. For example:

```text
REQUEST_FIELDS='["path", "method", "content_type", "headers", "cookies", "query", "path_params", "body"]'
```

The above is the default configuration for this setting, so if you are happy with that you don't
need to do anything. However, lets say you never want to log the request body, you could define
this in your environment and simply exclude `"body"` from that collection:

```text
REQUEST_FIELDS='["path", "method", "content_type", "headers", "cookies", "query", "path_params"]'
```

## Other Log Config

There are some other logging configurations that you can control via environment

### LOG_HTTP_EVENT & LOG_WORKER_EVENT

These define the value of the "event" key in the emitted log object.

By default, `LOG_HTTP_EVENT` is `"HTTP"` and `LOG_WORKER_EVENT` is `"Worker"`.

E.g., a log emitted by the HTTP handlers will be `{"event": "HTTP", ...}` and one emitted by the
worker will be `{"event": "Worker", ...}`.

### LOG_LEVEL

Set this according to the standard library logging levels. Any message emitted at a level that is
below this one will be silently (and efficiently, thanks to `structlog`) dropped.

For example, setting `LOG_LEVEL=WARNING` in your environment would mean that no `INFO` level logs
would ever be emitted by the application.

## More Goodies

### Automatic dropping of health check logs

Successful health check logs are dropped early in the processor chain. This prevents your logs
getting clogged up with "white noise" and all the associated data storage and ingestion costs that
go along with it.

Of course, if you health checks fail, there's nothing worse than those logs getting dropped too, so
any response from the health check handler not within the success status range is logged.

### Standard library logging config

We configure the standard library logger with a queue listener and handler and route any logs from
our dependencies through that, so they won't block the event loop.

### Environment specific processor chain

We inspect `stdout` destination to determine if it is writing to a terminal and modify the processor
chain so that you get pretty log output when developing locally!

## Worker Logging

### Worker.before_process

If logging configuration is enabled, we use this SAQ `Worker` hook to clear the structlog
contextvars for the job.

### Worker.after_process

If logging configuration is enabled, we use this SAQ `Worker` hook to extract the configured `Job`
attributes and inject them into the log, and emit the log event. The attributes that are logged for
each `Job` can be configured in
[`LogSettings`](../reference/starlite_saqlalchemy/settings/#starlite_saqlalchemy.settings.
LogSettings.JOB_FIELDS).

If the `Job.error` attribute is truthy, we log at `ERROR` severity, otherwise log at `INFO`.

## SAQ Logs

SAQ emits logs via standard library logging, we restrict these to level of `WARNING` or higher, and
handle them using the asyncio-friendly `queue_handler` that is provided to us by Starlite.

That means, you might see the following logs emitted from the SAQ logger:

### worker.py

#### `class Worker`

- upkeep(): l181 - EXCEPTION - on failed upkeep task
- process(): l253 - EXCEPTION - on job error
- process(): l270 - EXCEPTION - on after process hook failure

#### `def async_check_health()`

- l343 - WARNING - on health check failure
