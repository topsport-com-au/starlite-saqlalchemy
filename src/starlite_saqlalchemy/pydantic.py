from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, TypeVar

from pydantic import validator as pydantic_validator

if TYPE_CHECKING:
    from pydantic.typing import AnyCallable, AnyClassMethod

SQLAlchemyModel = TypeVar("SQLAlchemyModel")

_VALIDATORS: dict[str, dict[str, "AnyClassMethod"]] = defaultdict(dict)


def validator(
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool = True,
    whole: bool = True,
    allow_reuse: bool = False,
) -> Callable[["AnyCallable"], "AnyCallable"]:
    """Same as `pydantic.validator` but works with models created with the
    `dto` decorator."""

    def wrapper(f: "AnyCallable") -> "AnyCallable":
        dec = pydantic_validator(
            *fields,
            pre=pre,
            each_item=each_item,
            always=always,
            check_fields=check_fields,
            whole=whole,
            allow_reuse=allow_reuse,
        )
        cls_name, f_name = f.__qualname__.split(".", maxsplit=1)
        ref = f"{f.__module__}.{cls_name}"
        _VALIDATORS[ref][f_name] = dec(f)
        return dec

    return wrapper
