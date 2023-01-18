from starlite_saqlalchemy.constants import IS_SENTRY_SDK_INSTALLED

if not IS_SENTRY_SDK_INSTALLED:
    collect_ignore_glob = ["*"]
