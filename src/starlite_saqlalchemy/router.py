"""Dynamically generate routers."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from starlite import Dependency, get

from starlite_saqlalchemy.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from pydantic import BaseModel
    from starlite import HTTPRouteHandler
    from typing_extensions import LiteralString

    from starlite_saqlalchemy.service import Service

templates = {
    "get": "@get({params})",
    "async_def": "async def {fn_name}({params}) -> {return_type}:",
    "list_doc": '    """{resource} collection view."""',
    "service_param": "service: {service_type_name}",
    "filters_param": "filters: list[{filters_type_name}] = Dependency(skip_validation=True)",
    "list_return": "    return [{read_dto_name}.from_orm(item) for item in await service.list(*filters)]",
}


def create_collection_view(
    resource: LiteralString,
    read_dto_type: type[BaseModel],
    service_type: type[Service],
    filter_types: Iterable[Any] = (BeforeAfter, CollectionFilter, LimitOffset),
) -> HTTPRouteHandler:
    """Create a route handler for a collection view.

    Args:
        resource: name of the domain resource, e.g., "authors"
        read_dto_type: Pydantic model for serializing output.
        service_type: Service object to provide the view.
        filter_types: Collection filter types.

    Returns:
        A Starlite route handler.
    """
    namespace = {
        "Dependency": Dependency,
        "get": get,
        read_dto_type.__name__: read_dto_type,
        service_type.__name__: service_type,
        **{t.__name__: t for t in filter_types},
    }
    params = ", ".join(
        [
            templates["service_param"].format(service_type_name=service_type.__name__),
            templates["filters_param"].format(
                filters_type_name=" | ".join(f.__name__ for f in filter_types)
            ),
        ]
    )
    fn_name = f"get_{resource}"
    lines = [
        templates["get"].format(params=""),
        templates["async_def"].format(
            fn_name=fn_name,
            params=params,
            return_type=f"list[{read_dto_type.__name__}]",
        ),
        templates["list_doc"].format(resource=resource),
        templates["list_return"].format(read_dto_name=read_dto_type.__name__),
    ]
    script = "\n".join(lines)
    eval(  # nosec B307  # noqa: SCS101  # pylint: disable=eval-used
        compile(script, f"<generated_{resource}_{fn_name}>", "exec", dont_inherit=True),
        namespace,
    )
    return cast("HTTPRouteHandler", namespace[fn_name])
