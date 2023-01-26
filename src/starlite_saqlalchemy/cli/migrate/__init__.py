"""Migrate CLI entrypoint."""
from __future__ import annotations

import click


@click.group(name="migrate")
def entry_point() -> None:
    """Database migration commands."""
