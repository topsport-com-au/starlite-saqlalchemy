"""Worker CLI entry point."""
from __future__ import annotations

import click


@click.group(name="worker")
def entry_point() -> None:
    """Worker service commands."""
