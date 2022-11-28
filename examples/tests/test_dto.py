"""Tests for DTO examples."""
from examples.dto import minimal, minimal_configure_fields


def test_minimal_example() -> None:
    """Test the dto generated for the example."""
    assert minimal.WriteDTO.__fields__.keys() == {"id", "created", "updated", "name", "dob"}


def test_minimal_configure_fields() -> None:
    """Test expected fields in minimal example with configured fields."""
    assert minimal_configure_fields.WriteDTO.__fields__.keys() == {"name", "dob"}
