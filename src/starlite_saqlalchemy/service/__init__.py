"""Implementations for service object."""

from starlite_saqlalchemy import constants

from .generic import Service, make_service_callback

if constants.IS_SQLALCHEMY_INSTALLED:
    from .sqlalchemy import RepositoryService

__all__ = [
    "RepositoryService",
    "Service",
    "make_service_callback",
]
