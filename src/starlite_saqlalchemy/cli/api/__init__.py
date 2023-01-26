"""API CLI entry point."""
from __future__ import annotations

import click


@click.group(name="api")
def entry_point() -> None:
    """Commands for API service."""
