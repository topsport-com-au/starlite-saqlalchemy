"""Repository exception types."""
from __future__ import annotations


class RepositoryException(Exception):
    """Base repository exception type."""


class RepositoryConflictException(RepositoryException):
    """Exception for data integrity errors."""


class RepositoryNotFoundException(RepositoryException):
    """Identity not present in collection."""
