"""Tests for endpoint_decorator.py."""
from __future__ import annotations

import pytest

from starlite_saqlalchemy import endpoint_decorator


def test_endpoint_decorator() -> None:
    """Test for basic functionality."""

    @endpoint_decorator.endpoint(base_url="/something")
    class Endpoint:
        """Endpoints for something."""

        root = ""
        nested = "/somewhere"

    assert Endpoint.root == "/something/"
    assert Endpoint.nested == "/something/somewhere"


def test_endpoint_decorator_raises_if_no_base_url() -> None:
    """Test raising behavior when no base_url provided."""
    with pytest.raises(RuntimeError):

        @endpoint_decorator.endpoint
        class Endpoint:  # pylint: disable=unused-variable
            """whoops."""
