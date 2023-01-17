"""Tests for application ORM configuration."""
# pylint: disable=wrong-import-position,wrong-import-order
import pytest

pytest.importorskip("sqlalchemy")

import datetime
from unittest.mock import MagicMock

from starlite_saqlalchemy.db import orm


def test_sqla_touch_updated_timestamp() -> None:
    """Test that we are hitting the updated timestamp."""
    mock_session = MagicMock()
    mock_session.dirty = [MagicMock(), MagicMock()]
    orm.touch_updated_timestamp(mock_session)
    for mock_instance in mock_session.dirty:
        assert isinstance(mock_instance.updated, datetime.datetime)
