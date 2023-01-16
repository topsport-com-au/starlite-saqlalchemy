"""A context manager to support patching application settings."""
from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

    from pydantic import BaseSettings


@contextmanager
def modify_settings(*update: tuple[BaseSettings, dict[str, Any]]) -> Generator[None, None, None]:
    """Context manager that modify the desired settings and restore them on
    exit.

    >>> assert settings.app.ENVIRONMENT = "local"
    >>> with modify_settings((settings.app, {"ENVIRONMENT": "prod"})):
    >>>     assert settings.app.ENVIRONMENT == "prod"
    >>> assert settings.app.ENVIRONMENT == "local"
    """
    old_settings: list[tuple[BaseSettings, dict[str, Any]]] = []
    try:
        for model, new_values in update:
            old_values = {}
            for field, value in model.dict().items():
                if field in new_values:
                    old_values[field] = value
                    setattr(model, field, new_values[field])
            old_settings.append((model, old_values))
        yield
    finally:
        for model, old_values in old_settings:
            for field, old_val in old_values.items():
                setattr(model, field, old_val)
