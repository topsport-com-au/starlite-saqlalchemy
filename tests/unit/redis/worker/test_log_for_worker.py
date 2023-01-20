"""Tests for `starlite_saqlalchemy.log module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import structlog

from starlite_saqlalchemy import log

if TYPE_CHECKING:

    from pytest import MonkeyPatch
    from saq.job import Job
    from structlog.testing import CapturingLogger


async def test_before_process_calls_structlog_contextvars_clear_contextvars(
    monkeypatch: MonkeyPatch,
) -> None:
    """Ensure that we clear the structlog context in the worker before_process
    hook."""
    clear_ctx_vars_mock = MagicMock()
    monkeypatch.setattr(structlog.contextvars, "clear_contextvars", clear_ctx_vars_mock)
    await log.worker.before_process({})
    clear_ctx_vars_mock.assert_called_once()


async def test_after_process(job: Job, cap_logger: CapturingLogger) -> None:
    """Tests extraction of job data, and eventual log."""
    await log.worker.after_process({"job": job})
    assert [
        (
            "info",
            (),
            {
                "function": "whatever",
                "kwargs": {"a": "b"},
                "key": ANY,
                "scheduled": 0,
                "attempts": 0,
                "completed": 0,
                "queued": 0,
                "started": 0,
                "result": None,
                "error": None,
                "event": "Worker",
                "level": "info",
                "timestamp": ANY,
                "pickup_time_ms": 0,
                "completed_time_ms": 0,
                "total_time_ms": 0,
            },
        )
    ] == cap_logger.calls


async def test_after_process_logs_at_error(job: Job, cap_logger: CapturingLogger) -> None:
    """Tests eventual log is at ERROR level if `job.error`."""
    job.error = "Yep, this is the traceback."
    await log.worker.after_process({"job": job})
    assert [
        (
            "error",
            (),
            {
                "function": "whatever",
                "kwargs": {"a": "b"},
                "key": ANY,
                "scheduled": 0,
                "attempts": 0,
                "completed": 0,
                "queued": 0,
                "started": 0,
                "result": None,
                "error": "Yep, this is the traceback.",
                "event": "Worker",
                "level": "error",
                "timestamp": ANY,
                "pickup_time_ms": 0,
                "completed_time_ms": 0,
                "total_time_ms": 0,
            },
        )
    ] == cap_logger.calls
