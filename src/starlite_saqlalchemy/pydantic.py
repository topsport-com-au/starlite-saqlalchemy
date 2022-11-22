from collections import defaultdict
from typing import TYPE_CHECKING, Callable, TypeVar

from pydantic import validator as pydantic_validator

if TYPE_CHECKING:
    from pydantic.typing import AnyCallable, AnyClassMethod

SQLAlchemyModel = TypeVar("SQLAlchemyModel")

_VALIDATORS = defaultdict(dict)


def validator(
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool = True,
    whole: bool = None,
    allow_reuse: bool = False,
) -> Callable[["AnyCallable"], "AnyClassMethod"]:
    """Same as `pydantic.validator` but works with models created with the `dto` decorator."""
    def wrapper(f: "AnyCallable") -> "AnyClassMethod":
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
