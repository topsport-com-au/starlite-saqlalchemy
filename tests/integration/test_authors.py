from typing import TYPE_CHECKING

from httpx import AsyncClient

if TYPE_CHECKING:
    from starlite import Starlite


async def test_update_author(app: "Starlite") -> None:

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.put(
            "/authors/97108ac1-ffcb-411d-8b1e-d9183399f63b",
            json={"name": "TEST UPDATE", "dob": "1890-9-15"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "TEST UPDATE"
