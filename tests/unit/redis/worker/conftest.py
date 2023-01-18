from starlite_saqlalchemy.constants import IS_SAQ_INSTALLED

if not IS_SAQ_INSTALLED:
    collect_ignore_glob = ["*"]
