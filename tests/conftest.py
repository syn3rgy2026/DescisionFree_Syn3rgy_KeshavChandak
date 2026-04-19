"""Pytest setup: project root on path and cwd so config paths resolve."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _project_root_on_path_and_cwd() -> None:
    sys.path.insert(0, str(ROOT))
    prev = os.getcwd()
    os.chdir(ROOT)
    yield
    os.chdir(prev)
