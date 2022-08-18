from starlette.status import HTTP_200_OK
from starlite.testing import TestClient

from examples import basic_example


def test_basic_example() -> None:
    with TestClient(app=basic_example.app) as client:
        response = client.get("/example")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}
