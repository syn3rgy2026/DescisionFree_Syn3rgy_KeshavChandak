"""Tests for code runner helpers (load module in isolation — avoids tools/__init__.py)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def crc():
    path = ROOT / "tools" / "code_runner_tool.py"
    spec = importlib.util.spec_from_file_location(
        "_code_runner_tool_isolated",
        path,
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_format_result_success(crc):
    s = crc._format_result({"exit_code": 0, "stdout": "ok", "stderr": ""})
    assert "SUCCESS" in s
    assert "ok" in s


def test_format_result_failure(crc):
    s = crc._format_result({"exit_code": 2, "stdout": "", "stderr": "bad"})
    assert "FAILED" in s
    assert "bad" in s


def test_run_lint_valid_json(tmp_path: Path, crc):
    p = tmp_path / "x.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert "No syntax errors" in crc.run_lint(str(p))


def test_run_lint_invalid_json(tmp_path: Path, crc):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    out = crc.run_lint(str(p))
    assert "FAILED" in out or "Expecting" in out


def test_run_lint_valid_py(tmp_path: Path, crc):
    p = tmp_path / "m.py"
    p.write_text("x = 1\n", encoding="utf-8")
    out = crc.run_lint(str(p))
    assert "No syntax errors" in out or "SUCCESS" in out
