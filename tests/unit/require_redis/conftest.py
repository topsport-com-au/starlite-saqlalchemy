from starlite_saqlalchemy.constants import IS_REDIS_INSTALLED

if not IS_REDIS_INSTALLED:
    collect_ignore_glob = ["*"]
