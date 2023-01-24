"""Docs CLI entry point."""
from __future__ import annotations

import click


@click.group(name="docs")
def entry_point() -> None:
    """Commands for building and releasing docs."""
