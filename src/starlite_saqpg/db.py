import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any
from uuid import UUID

from orjson import dumps, loads
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from .config import db_settings

if TYPE_CHECKING:
    from starlite.datastructures import State
    from starlite.types import Message


__all__ = [
    "AsyncScopedSession",
    "engine",
    "async_session_factory",
]


def _default(val: Any) -> str:
    if isinstance(val, UUID):
        return str(val)
    raise TypeError()


engine = create_async_engine(
    db_settings.URL,
    echo=db_settings.ECHO,
    echo_pool=db_settings.ECHO_POOL,
    json_serializer=partial(dumps, default=_default),
    max_overflow=db_settings.POOL_MAX_OVERFLOW,
    pool_size=db_settings.POOL_SIZE,
    pool_timeout=db_settings.POOL_TIMEOUT,
    poolclass=NullPool if db_settings.POOL_DISABLE else None,
)
"""Configure via [DatabaseSettings][starlite_saqpg.config.DatabaseSettings]. Overrides default JSON 
serializer to use `orjson`. See [`create_async_engine()`][sqlalchemy.ext.asyncio.create_async_engine]
for detailed instructions.
"""
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
"""
Database session factory. See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
"""


@event.listens_for(engine.sync_engine, "connect")
def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:
    """
    Using orjson for serialization of the json column values means that the output is binary, not
    `str` like `json.dumps` would output.

    SQLAlchemy expects that the json serializer returns `str` and calls `.encode()` on the value to
    turn it to bytes before writing to the JSONB column. I'd need to either wrap `orjson.dumps` to
    return a `str` so that SQLAlchemy could then convert it to binary, or do the following, which
    changes the behaviour of the dialect to expect a binary value from the serializer.

    See Also https://github.com/sqlalchemy/sqlalchemy/blob/14bfbadfdf9260a1c40f63b31641b27fe9de12a0/lib/sqlalchemy/dialects/postgresql/asyncpg.py#L934
    """

    def encoder(bin_value: bytes) -> bytes:
        # \x01 is the prefix for jsonb used by PostgreSQL.
        # asyncpg requires it when format='binary'
        return b"\x01" + bin_value

    def decoder(bin_value: bytes) -> Any:
        # the byte is the \x01 prefix for jsonb used by PostgreSQL.
        # asyncpg returns it when format='binary'
        return loads(bin_value[1:])

    dbapi_connection.await_(
        dbapi_connection.driver_connection.set_type_codec(
            "jsonb",
            encoder=encoder,
            decoder=decoder,
            schema="pg_catalog",
            format="binary",
        )
    )


AsyncScopedSession = async_scoped_session(async_session_factory, scopefunc=asyncio.current_task)
"""
Scopes [`AsyncSession`][sqlalchemy.ext.asyncio.AsyncSession] instance to current task using
[`asyncio.current_task()`][asyncio.current_task].

Care must be taken that [`AsyncScopedSession.remove()`][sqlalchemy.ext.asyncio.async_scoped_session.remove] 
is called as late as possible during each task. This is managed by the 
[`Starlite.after_request`][starlite.app.Starlite] lifecycle hook.
"""


async def transaction_manager(message: "Message", _: "State") -> None:
    """
    Register to `Starlite.config.AppConfig.before_send`.

    Try to have as close as possible to last in line of `before_send` handlers to minimize
    possibility of an error occurring after database commit.

    Per SQLAlchemy docs:

        > Using current_task() for the “key” in the scope requires that the
        > `async_scoped_session.remove()` method is called from within the outermost awaitable, to
        > ensure the key is removed from the registry when the task is complete, otherwise the task
        > handle as well as the AsyncSession will remain in memory, essentially creating a memory
        > leak. See the following example which illustrates the correct use of
        > `async_scoped_session.remove().`

        They don't recommend `AsyncScopedSession`, but it's working well enough for me at the
        moment.

    Parameters
    ----------
    message : Message
        Either a HTTP or Websocket send message.
    _ : State
        The `Starlite` application state object.

    Returns
    -------

    """
    if message["type"] == "http.response.start":
        try:
            if 200 <= message["status"] < 300:
                await AsyncScopedSession.commit()
            else:
                await AsyncScopedSession.rollback()
        finally:
            await AsyncScopedSession.remove()
