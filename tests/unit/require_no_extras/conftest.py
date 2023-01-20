"""Tests are only run if no extra dependencies are installed."""

from starlite_saqlalchemy import constants

SKIP = any(
    [
        constants.IS_SAQ_INSTALLED,
        constants.IS_SENTRY_SDK_INSTALLED,
        constants.IS_REDIS_INSTALLED,
        constants.IS_SQLALCHEMY_INSTALLED,
    ]
)

if SKIP:
    collect_ignore_glob = ["*"]
