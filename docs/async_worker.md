# Async Worker

- Integrated asynchronous worker for processing background jobs.
- Pattern is built on [SAQ](https://github.com/tobymao/saq) ([why SAQ?](#why-saq))

## Service object integration

You can leverage the async worker without needing to know anything specific about the worker
implementation.

The generic [Service](../reference/starlite_saqlalchemy/service/#starlite_saqlalchemy.service.Service)
object includes a method that allows you to enqueue a background task.

### Example

Let's add a background task that sends an email whenever a new `Author` is created.

```python
from typing import Any
from starlite_saqlalchemy import worker
from starlite_saqlalchemy import service
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository

from domain.authors import Author, ReadDTO


class Repository(SQLAlchemyRepository[Author]):
    model_type = Author


class Service(service.RepositoryService[Author]):
    """Author service object."""

    repository_type = Repository

    async def create(self, data: Author) -> Author:
        created = await super().create(data)
        await worker.enqueue_background_task_for_service(
            "send_author_created_email", self , raw_author=ReadDTO.from_orm(created).dict()
        )
        return created

    async def send_author_created_email(self, raw_author: dict[str, Any]) -> None:
        """Logic here to send the email."""
```

## Don't block the event loop

It is important to remember that this worker runs on the same event loop as the application itself,
so be mindful that the operations you do in background tasks aren't blocking the loop.

If you need to do computationally heavy work in background tasks, a better pattern would be to use a
something like [Honcho](https://honcho.readthedocs.io/en/latest/) to start an SAQ worker in a
different process to the Starlite application, and run your app in a multicore environment.

## Why SAQ

I like that it leverages [`BLMOVE`](https://redis.io/commands/blmove/) instead of polling to wait
for jobs: see [Pattern: Reliable queue](https://redis.io/commands/lmove/).

SAQ also make a direct comparison to `ARQ` in their
[`README`](https://github.com/tobymao/saq/blob/master/README.md#comparison-to-arq), so I'll let that
speak for itself:

> SAQ is heavily inspired by [ARQ](https://github.com/samuelcolvin/arq) but has several
> enhancements.
>
> 1. Avoids polling by leveraging [BLMOVE](https://redis.io/commands/blmove) or
>    [RPOPLPUSH](https://redis.io/commands/rpoplpush) and NOTIFY
>     i. SAQ has much lower latency than ARQ, with delays of < 5ms. ARQ's default polling frequency
>        is 0.5 seconds
>     ii. SAQ is up to [8x faster](benchmarks) than ARQ
> 2. Web interface for monitoring queues and workers
> 3. Heartbeat monitor for abandoned jobs
> 4. More robust failure handling
>     i. Storage of stack traces
>     ii. Sweeping stuck jobs
>     iii. Handling of cancelled jobs different from failed jobs (machine redeployments)
> 5. Before and after job hooks
> 6. Easily run multiple workers to leverage more cores
