"""Things that make working with DTOs nicer."""
from __future__ import annotations

from typing import TYPE_CHECKING

from starlite_saqlalchemy import settings

from .types import DTOConfig, Field, Mark, Purpose

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Any, Literal

    from pydantic.fields import FieldInfo

__all__ = (
    "config",
    "field",
)


def config(
    purpose: Purpose | Literal["read", "write"] = Purpose.WRITE,
    exclude: set[str] | None = None,
) -> DTOConfig:
    """
    Args:
        purpose: Is the DTO for parsing "write" data, or serializing "read" data?
        exclude: Omit fields from dto by key name.

    Returns:
        `DTOConfig` object configured per parameters.
    """
    exclude = set() if exclude is None else exclude
    return DTOConfig(purpose=Purpose(purpose), exclude=exclude)


def field(
    mark: Mark | Literal["read-only", "skip"] | None = None,
    pydantic_type: Any | None = None,
    pydantic_field: FieldInfo | None = None,
    validators: Iterable[Callable[[Any], Any]] | None = None,
) -> dict[str, Field]:
    """Construct a `dto.Field()` instances.

    Args:
        mark: How this field should be treated by the model factory.
        pydantic_type: Override the type annotation for this field.
        pydantic_field: Result of Pydantic's `Field()` function. Override the `FieldInfo` instance
            used by the generated model.
        validators: Added to the generated model as validators, with `allow_reuse=True`.
    """
    return {
        settings.api.DTO_INFO_KEY: Field(
            mark=Mark(mark) if mark is not None else mark,
            pydantic_type=pydantic_type,
            pydantic_field=pydantic_field,
            validators=validators,
        )
    }
