"""Test settings module."""
import pytest

from starlite_saqlalchemy.utils import slugify


@pytest.mark.parameterized(
    ("value_to_slugify", "expected_slug"),
    [
        ("value-to-slugify", "value-to-slugify"),
        ("value to slugify", "value-to-slugify"),
        ("value         to.slugify", "value-to-slugify"),
        ("value!! to SLugify", "value-to-slugify"),
        ("value!! to ___SLugify", "value-to-slugify"),
    ],
)
def test_slugify(value_to_slugify: str, expected_slug: str) -> None:
    """Test app name conversion to slug."""
    assert slugify(value_to_slugify) == expected_slug
