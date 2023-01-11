"""General utility functions."""
import dataclasses
from typing import Any


def dataclass_as_dict_shallow(dataclass: Any, *, exclude_none: bool = False) -> dict[str, Any]:
    """Convert a dataclass to dict, without deepcopy."""
    ret: dict[str, Any] = {}
    for field in dataclasses.fields(dataclass):
        value = getattr(dataclass, field.name)
        if exclude_none and value is None:
            continue
        ret[field.name] = value
    return ret
