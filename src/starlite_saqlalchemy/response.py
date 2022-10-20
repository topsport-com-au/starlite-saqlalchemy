from typing import Any

import starlite
from asyncpg.pgproto import pgproto
from starlite.response import Response as _Response

__all__ = ["Response"]


class Response(_Response):
    """Custom [`starlite.Response`][starlite.response.Response] that handles
    serialization of the postgres UUID type used by SQLAlchemy."""

    @staticmethod
    def serializer(value: Any) -> Any:
        """Serializes `value`.

        Parameters
        ----------
        value : Any
            The thing to be serialized.

        Returns
        -------
        Any
            Serialized representation of `value`.
        """
        if isinstance(value, pgproto.UUID):
            return str(value)
        return starlite.Response.serializer(value)
