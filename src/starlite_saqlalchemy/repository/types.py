"""Repository type definitions."""
from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)

FilterTypes = BeforeAfter | CollectionFilter | LimitOffset
"""Aggregate type alias of the types supported for collection filtering."""
