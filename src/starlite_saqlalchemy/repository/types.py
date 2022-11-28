"""Repository type definitions."""
from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy.orm import DeclarativeBase

from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)

FilterTypes = BeforeAfter | CollectionFilter[Any] | LimitOffset
"""Aggregate type alias of the types supported for collection filtering."""


T = TypeVar("T")


ModelT = TypeVar("ModelT", bound=DeclarativeBase)
