from starlite_saqlalchemy.constants import IS_SQLALCHEMY_INSTALLED

if not IS_SQLALCHEMY_INSTALLED:
    collect_ignore_glob = ["*"]
