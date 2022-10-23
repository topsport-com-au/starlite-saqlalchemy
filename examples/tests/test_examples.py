"""Tests the documentation examples."""
from starlette.status import HTTP_200_OK
from starlite.testing import TestClient

from examples import basic_example


def test_basic_example() -> None:
    """A simple in/out test of the hello-world example."""
    with TestClient(app=basic_example.app) as client:
        response = client.get("/example")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}
