"""Tests for application ORM configuration."""
import datetime
from unittest.mock import MagicMock

from starlite_saqlalchemy.db import orm
from tests.utils.domain import Author, CreateDTO


def test_sqla_touch_updated_timestamp() -> None:
    """Test that we are hitting the updated timestamp."""
    mock_session = MagicMock()
    mock_session.dirty = [MagicMock(), MagicMock()]
    orm.touch_updated_timestamp(mock_session)
    for mock_instance in mock_session.dirty:
        assert isinstance(mock_instance.updated, datetime.datetime)


def test_from_dto() -> None:
    """Test conversion of a DTO instance to a model instance."""
    data = CreateDTO(name="someone", dob="1982-03-22")
    author = Author.from_dto(data)
    assert author.name == "someone"
    assert author.dob == datetime.date(1982, 3, 22)
