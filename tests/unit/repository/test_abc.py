from unittest.mock import MagicMock

import pytest

from starlite_saqlalchemy.repository.exceptions import RepositoryNotFoundException
from tests.unit.utils import GenericMockRepository


def test_repository_check_not_found_raises() -> None:
    with pytest.raises(RepositoryNotFoundException):
        GenericMockRepository.check_not_found(None)


def test_repository_check_not_found_returns_item() -> None:
    mock_item = MagicMock()
    assert GenericMockRepository.check_not_found(mock_item) is mock_item
