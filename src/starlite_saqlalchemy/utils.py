"""General utility functions."""
import dataclasses
import unicodedata
from typing import Any, cast

try:
    import re2 as re  # pyright: ignore
except ImportError:
    import re


def case_insensitive_string_compare(a: str, b: str, /) -> bool:
    """Compare `a` and `b`, stripping whitespace and ignoring case."""
    return a.strip().lower() == b.strip().lower()


def dataclass_as_dict_shallow(dataclass: Any, *, exclude_none: bool = False) -> dict[str, Any]:
    """Convert a dataclass to dict, without deepcopy."""
    ret: dict[str, Any] = {}
    for field in dataclasses.fields(dataclass):
        value = getattr(dataclass, field.name)
        if exclude_none and value is None:
            continue
        ret[field.name] = value
    return ret


def slugify(value: str, allow_unicode: bool = False, separator: str = "-") -> str:
    """slugify.

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Args:
        value (str): the string to slugify
        allow_unicode (bool, optional): allow unicode characters in slug. Defaults to False.
        separator(str, optional): the delimiter to use for word boundaries.  Defaults to '-'
    Returns:
        str: a slugified string of the value parameter
    """
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return cast("str", re.sub(r"[-\s]+", separator, value).strip(f"{separator}_"))
