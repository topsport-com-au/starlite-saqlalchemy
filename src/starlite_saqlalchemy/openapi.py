"""Application OpenAPI config."""
from __future__ import annotations

from pydantic_openapi_schema.v3_1_0 import Contact
from starlite import OpenAPIConfig

from starlite_saqlalchemy import settings

config = OpenAPIConfig(
    title=settings.openapi.TITLE or settings.app.NAME,
    version=settings.openapi.VERSION,
    contact=Contact(name=settings.openapi.CONTACT_NAME, email=settings.openapi.CONTACT_EMAIL),
    use_handler_docstrings=True,
)
"""OpenAPI config for app, see [OpenAPISettings][starlite_saqlalchemy.settings.OpenAPISettings]"""
