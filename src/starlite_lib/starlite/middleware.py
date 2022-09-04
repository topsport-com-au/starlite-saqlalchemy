import logging

from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlite.middleware import MiddlewareProtocol

from .db import AsyncScopedSession

__all__ = ["DBSessionMiddleware"]

logger = logging.getLogger(__name__)


class DBSessionMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    @staticmethod
    async def _manage_session(message: Message) -> None:
        logger.debug("_manage_session() called: %s", message)
        if 200 <= message["status"] < 300:
            await AsyncScopedSession.commit()
            logger.debug("session committed")
        else:
            await AsyncScopedSession.rollback()
            logger.debug("session rolled back")
        await AsyncScopedSession.remove()
        logger.debug("session removed")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    await self._manage_session(message)
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
