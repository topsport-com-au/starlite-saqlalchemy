"""Integration tests for the test Author domain."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.xfail()
async def test_update_author(client: AsyncClient) -> None:
    """Integration test for PUT route."""
    response = await client.put(
        "/authors/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "TEST UPDATE", "dob": "1890-9-15"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "TEST UPDATE"
