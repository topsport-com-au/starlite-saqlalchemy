from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from starlite_saqlalchemy.constants import IS_SAQ_INSTALLED

if TYPE_CHECKING:
    from saq.job import Job

if not IS_SAQ_INSTALLED:
    collect_ignore_glob = ["*"]


@pytest.fixture()
def job() -> Job:
    """SAQ Job instance."""

    from saq.job import Job

    return Job(function="whatever", kwargs={"a": "b"})
