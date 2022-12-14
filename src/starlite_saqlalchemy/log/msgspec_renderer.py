"""A JSON Renderer for structlog using msgspec.

Msgspec doesn't have an API consistent with the stdlib's `json` module,
which is required for structlog's `JSONRenderer`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from structlog.typing import EventDict, WrappedLogger


_encoder = msgspec.json.Encoder()


def msgspec_json_renderer(_: WrappedLogger, __: str, event_dict: EventDict) -> bytes:
    """Structlog processor that uses `msgspec` for JSON encoding.

    Args:
        _ ():
        __ ():
        event_dict (): The data to be logged.

    Returns:
        The log event encoded to JSON by msgspec.
    """
    return _encoder.encode(event_dict)
