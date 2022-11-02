"""Default serializer used by plugin if one not provided."""
from typing import Any

from asyncpg.pgproto import pgproto
from starlite import Response


def default_serializer(value: Any) -> Any:
    """Serialize `value`.

    Args:
        value: To be serialized.

    Returns:
        Serialized representation of `value`.
    """
    if isinstance(value, pgproto.UUID):
        return str(value)
    return Response[Any].serializer(value)
