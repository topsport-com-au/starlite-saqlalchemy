from functools import partial
from typing import Any
from uuid import UUID

from orjson import dumps, loads
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import db_settings

__all__ = [
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
)
"""Configure via [DatabaseSettings][starlite_lib.config.DatabaseSettings]. Overrides default JSON 
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
