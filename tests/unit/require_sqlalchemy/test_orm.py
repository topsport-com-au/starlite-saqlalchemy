"""Tests for application ORM configuration."""

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


def test_sqla_touch_updated_no_updated() -> None:
    """Test that we don't hit the updated timestamp if model doesn't have
    one."""

    class Model(orm.Base):
        """orm.Base has no 'updated' attribute."""

    instance = Model()
    assert "updated" not in vars(instance)
    mock_session = MagicMock(dirty=[instance])
    orm.touch_updated_timestamp(mock_session)
    assert "updated" not in vars(instance)
