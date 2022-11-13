"""Test settings module."""
from starlite_saqlalchemy import settings


def test_app_slug() -> None:
    """Test app name conversion to slug."""
    assert settings.app.slug == "my-starlite-app"
