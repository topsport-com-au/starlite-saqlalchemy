"""Tests for the repository base class."""
from unittest.mock import MagicMock

import pytest

from starlite_saqlalchemy.repository.exceptions import RepositoryNotFoundException
from starlite_saqlalchemy.testing.repository import GenericMockRepository


def test_repository_check_not_found_raises() -> None:
    """Test `check_not_found()` raises if `None`."""
    with pytest.raises(RepositoryNotFoundException):
        GenericMockRepository.check_not_found(None)


def test_repository_check_not_found_returns_item() -> None:
    """Test `check_not_found()` returns the item if not `None`."""
    mock_item = MagicMock()
    assert GenericMockRepository.check_not_found(mock_item) is mock_item
