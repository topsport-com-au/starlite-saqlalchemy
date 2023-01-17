"""Tests for sentry integration."""
# pylint: disable=wrong-import-position,wrong-import-order
import pytest

pytest.importorskip("sentry_sdk")

from typing import TYPE_CHECKING

from starlite_saqlalchemy import settings
from starlite_saqlalchemy.sentry import SamplingContext, sentry_traces_sampler

if TYPE_CHECKING:
    from starlite.types.asgi_types import HTTPScope


@pytest.mark.parametrize(
    ("path", "sample_rate"),
    [("/watever", settings.sentry.TRACES_SAMPLE_RATE), (settings.api.HEALTH_PATH, 0.0)],
)
def test_sentry_traces_sampler(http_scope: "HTTPScope", path: str, sample_rate: float) -> None:
    """Test that traces sampler correctly ignore health requests."""
    http_scope["path"] = path
    sentry_context = SamplingContext(
        asgi_scope=http_scope, parent_sampled=None, transaction_context={}
    )
    assert sentry_traces_sampler(sentry_context) == sample_rate
