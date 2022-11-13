"""Tests for the default response serializer."""
from __future__ import annotations

from uuid import uuid4

from asyncpg.pgproto import pgproto

from starlite_saqlalchemy import serializer


def test_pg_uuid_serialization() -> None:
    py_uuid = uuid4()
    pg_uuid = pgproto.UUID(py_uuid.bytes)
    assert serializer.default_serializer(pg_uuid) == str(py_uuid)
