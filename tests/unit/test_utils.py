"""Test settings module."""
import pytest

from starlite_saqlalchemy.utils import slugify


@pytest.mark.parametrize(
    ("slug", "expected_slug"),
    [
        ("value-to-slugify", "value-to-slugify"),
        ("value to slugify", "value-to-slugify"),
        ("value         to.slugify", "value-toslugify"),
        ("value!! to SLugify", "value-to-slugify"),
        ("value!! to ___SLugify", "value-to-___slugify"),
    ],
)
def test_slugify(slug: str, expected_slug: str) -> None:
    """Test app name conversion to slug."""
    assert slugify(value=slug) == expected_slug
