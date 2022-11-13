"""Test testing module."""

import pytest

from starlite_saqlalchemy import testing
from starlite_saqlalchemy.repository.exceptions import RepositoryConflictException
from tests.utils import domain


async def test_repo_raises_conflict_if_add_with_id() -> None:
    """Test mock repo raises conflict if add identified entity."""
    author, _ = await domain.Service().list()
    with pytest.raises(RepositoryConflictException):
        await testing.GenericMockRepository[domain.Author]().add(author)
