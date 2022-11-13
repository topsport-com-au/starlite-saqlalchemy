"""Tests for db module."""
# pylint: disable=protected-access
from __future__ import annotations

from uuid import uuid4

import pytest

from starlite_saqlalchemy import db


def test_serializer_default() -> None:
    """Test _default() function serializes UUID."""
    val = uuid4()
    assert db._default(val) == str(val)


def test_serializer_raises_type_err() -> None:
    """Test _default() function raises ValueError."""
    with pytest.raises(TypeError):
        db._default(None)
