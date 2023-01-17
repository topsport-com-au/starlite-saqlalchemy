"""Tests for the SAQ async worker functionality."""
from __future__ import annotations

from asyncpg.pgproto import pgproto

from starlite_saqlalchemy import worker
from tests.utils.domain.authors import Author, ReadDTO


def test_worker_decoder_handles_pgproto_uuid() -> None:
    """Test that the decoder can handle pgproto.UUID instances."""
    pg_uuid = pgproto.UUID("0448bde2-7c69-4e6b-9c03-7b217e3b563d")
    encoded = worker.encoder.encode(pg_uuid)
    assert encoded == b'"0448bde2-7c69-4e6b-9c03-7b217e3b563d"'


def test_worker_decoder_handles_pydantic_models(authors: list[Author]) -> None:
    """Test that the decoder we use for SAQ will encode a pydantic model."""
    pydantic_model = ReadDTO.from_orm(authors[0])
    encoded = worker.encoder.encode(pydantic_model)
    assert (
        encoded
        == b'{"created":"0001-01-01T00:00:00","updated":"0001-01-01T00:00:00","id":"97108ac1-ffcb-411d-8b1e-d9183399f63b","name":"Agatha Christie","dob":"1890-09-15"}'
    )
