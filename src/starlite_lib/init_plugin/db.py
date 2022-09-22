import asyncio
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_scoped_session

from starlite_lib.db import async_session_factory

if TYPE_CHECKING:
    from starlite.datastructures import State
    from starlite.types import Message

__all__ = ["AsyncScopedSession"]


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
