"""Integration tests for HTTP logging."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import UUID

from httpx import AsyncClient

if TYPE_CHECKING:
    from starlite import Starlite
    from structlog.testing import CapturingLogger


async def test_health_logging_skipped(app: Starlite, cap_logger: CapturingLogger) -> None:
    """Integration test for PUT route."""

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200

    assert [] == cap_logger.calls


async def test_logging(app: "Starlite", cap_logger: CapturingLogger) -> None:
    """Integration test for logging."""

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.put(
            "/authors/97108ac1-ffcb-411d-8b1e-d9183399f63b",
            json={"name": "LOGMAN", "dob": "1990-9-15"},
        )
        assert response.status_code == 200

    assert cap_logger.calls == [
        (
            "info",
            (),
            {
                "event": "HTTP",
                "response": {
                    "status_code": 200,
                    "cookies": {},
                    "headers": {"content-type": "application/json", "content-length": "151"},
                    "body": ANY,
                },
                "request": {
                    "path": "/authors/97108ac1-ffcb-411d-8b1e-d9183399f63b",
                    "method": "PUT",
                    "headers": {
                        "host": "testserver",
                        "accept": "*/*",
                        "accept-encoding": "gzip, deflate",
                        "connection": "keep-alive",
                        "user-agent": ANY,
                        "content-length": "38",
                        "content-type": "application/json",
                    },
                    "cookies": {},
                    "query": b"",
                    "path_params": {"author_id": UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b")},
                    "body": b'{"name": "LOGMAN", "dob": "1990-9-15"}',
                },
                "level": "info",
                "timestamp": ANY,
            },
        )
    ]
