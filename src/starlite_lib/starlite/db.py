import asyncio

from sqlalchemy.ext.asyncio import async_scoped_session

from starlite_lib.db import async_session_factory

__all__ = ["AsyncScopedSession"]


AsyncScopedSession = async_scoped_session(async_session_factory, scopefunc=asyncio.current_task)
"""
Scopes [`AsyncSession`][sqlalchemy.ext.asyncio.AsyncSession] instance to current task using
[`asyncio.current_task()`][asyncio.current_task].

Care must be taken that [`AsyncScopedSession.remove()`][sqlalchemy.ext.asyncio.async_scoped_session.remove] 
is called as late as possible during each task. This is managed by the 
[`Starlite.after_request`][starlite.app.Starlite] lifecycle hook.
"""
