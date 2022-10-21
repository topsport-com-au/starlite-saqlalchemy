"""Test for the application cache configurations."""
from typing import TYPE_CHECKING

from starlite.config.cache import default_cache_key_builder
from starlite.testing import RequestFactory

from starlite_saqlalchemy import cache, settings

if TYPE_CHECKING:
    import pytest


def test_cache_key_builder(monkeypatch: "pytest.MonkeyPatch") -> None:
    """Test that the cache key builder prefixes cache keys."""
    monkeypatch.setattr(settings.AppSettings, "slug", "sllluuugg")
    request = RequestFactory().get("/test")
    default_cache_key = default_cache_key_builder(request)
    assert cache.cache_key_builder(request) == f"sllluuugg:{default_cache_key}"
