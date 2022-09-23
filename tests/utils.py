from typing import Any

import requests
from starlite import Starlite
from starlite.testing import TestClient

from starlite_lib import ConfigureApp


def make_test_client_request(
    handlers: list, route: str, method: str = "GET", **kwargs: Any
) -> requests.Response:
    app = Starlite(route_handlers=handlers, on_app_init=[ConfigureApp()], **kwargs)
    with TestClient(app=app) as client:
        return client.request(method, route)
