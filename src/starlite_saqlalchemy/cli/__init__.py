"""CLI for starlite-saqlalchemy.

Examples `$ ssql --help`
"""
from __future__ import annotations

import click

from starlite_saqlalchemy.constants import IS_SAQ_INSTALLED, IS_SQLALCHEMY_INSTALLED

from . import api


@click.group()
def entry_point() -> None:
    """Starlite-saqlalchemy."""


entry_point.add_command(api.entry_point)

if IS_SAQ_INSTALLED:
    from . import worker

    entry_point.add_command(worker.entry_point)

if IS_SQLALCHEMY_INSTALLED:
    from . import migrate

    entry_point.add_command(migrate.entry_point)
