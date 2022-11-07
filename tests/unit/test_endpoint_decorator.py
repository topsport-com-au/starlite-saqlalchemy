from __future__ import annotations

import pytest

from starlite_saqlalchemy import endpoint_decorator


def test_endpoint_decorator() -> None:
    @endpoint_decorator.endpoint(base_url="/something")
    class Endpoint:
        root = ""
        nested = "/somewhere"

    assert Endpoint.root == "/something/"
    assert Endpoint.nested == "/something/somewhere"


def test_endpoint_decorator_raises_if_no_base_url() -> None:
    with pytest.raises(RuntimeError):

        @endpoint_decorator.endpoint
        class Endpoint:
            ...
