"""Tests for behavior of the health check access log filter."""
from logging import LogRecord

from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from starlite_saqlalchemy import logging, settings


def test_access_log_filter_status_ok() -> None:
    """Ensure that 200 responses to the heath check route are not logged."""
    log_record = LogRecord(
        name="test.log",
        level=1,
        pathname="pathname",
        lineno=1,
        msg="message",
        args=("", settings.api.HEALTH_PATH, "", HTTP_200_OK),
        exc_info=None,
    )
    log_filter = logging.AccessLogFilter(path_re=settings.api.HEALTH_PATH)
    assert log_filter.filter(log_record) is False


def test_access_log_filter_status_not_ok() -> None:
    """Ensure that non-200 responses to the heath check route are logged."""
    log_record = LogRecord(
        name="test.log",
        level=1,
        pathname="pathname",
        lineno=1,
        msg="message",
        args=("", settings.api.HEALTH_PATH, "", HTTP_503_SERVICE_UNAVAILABLE),
        exc_info=None,
    )
    log_filter = logging.AccessLogFilter(path_re=settings.api.HEALTH_PATH)
    assert log_filter.filter(log_record) is True
