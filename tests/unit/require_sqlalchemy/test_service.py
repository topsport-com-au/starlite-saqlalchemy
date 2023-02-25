"""Tests for Service object patterns."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from starlite_saqlalchemy import service
from starlite_saqlalchemy.exceptions import NotFoundError
from tests.utils import domain

if TYPE_CHECKING:
    from starlite_saqlalchemy.testing.generic_mock_repository import (
        GenericMockRepository,
    )


@pytest.fixture(autouse=True)
def _patch_author_service(
    author_repository_type: GenericMockRepository,  # pylint: disable=unused-argument
) -> None:
    """Patch the repository for all tests."""


async def test_service_create() -> None:
    """Test repository create action."""
    resp = await domain.authors.Service().create(
        domain.authors.Author(name="someone", dob=date.min),
    )
    assert resp.name == "someone"
    assert resp.dob == date.min


async def test_service_list() -> None:
    """Test repository list action."""
    items = await domain.authors.Service().list()
    assert isinstance(items, tuple)
    assert len(items) == 2


async def test_service_update() -> None:
    """Test repository update action."""
    service_obj = domain.authors.Service()
    authors = await service_obj.list()
    author = authors[0]
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.update(author.id, author)
    assert resp.name == "different"


async def test_service_upsert_update() -> None:
    """Test repository upsert action for update."""
    service_obj = domain.authors.Service()
    authors = await service_obj.list()
    author = authors[0]
    assert author.name == "Agatha Christie"
    author.name = "different"
    resp = await service_obj.upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "different"


async def test_service_upsert_create() -> None:
    """Test repository upsert action for create."""
    author = domain.authors.Author(id=uuid4(), name="New Author")
    resp = await domain.authors.Service().upsert(author.id, author)
    assert resp.id == author.id
    assert resp.name == "New Author"


async def test_service_get_by_id() -> None:
    """Test repository get action."""
    service_obj = domain.authors.Service()
    authors = await service_obj.list()
    author = authors[0]
    retrieved = await service_obj.get_by_id(author.id)
    assert author is retrieved


async def test_service_get_one_or_none() -> None:
    """Test repository get action."""
    service_obj = domain.authors.Service()
    authors = await service_obj.list()
    author = authors[0]
    retrieved = await service_obj.get_one_or_none(id=author.id)
    assert author is retrieved


async def test_service_delete() -> None:
    """Test repository delete action."""
    service_obj = domain.authors.Service()
    authors = await service_obj.list()
    author = authors[0]
    deleted = await service_obj.delete(author.id)
    assert author is deleted


async def test_service_new_context_manager() -> None:
    """Simple test of `Service.new()` context manager behavior."""
    async with service.Service[domain.authors.Author].new() as service_obj:
        assert isinstance(service_obj, service.Service)


async def test_service_method_default_behavior() -> None:
    """Test default behavior of base service methods."""
    service_obj = service.Service[object]()
    data = object()
    assert await service_obj.count() == 0
    assert await service_obj.create(data) is data
    assert await service_obj.list() == []
    assert await service_obj.list_and_count() == ([], 0)
    assert await service_obj.update("abc", data) is data
    assert await service_obj.upsert("abc", data) is data
    with pytest.raises(NotFoundError):
        await service_obj.get_by_id("abc")
    with pytest.raises(NotFoundError):
        await service_obj.delete("abc")
