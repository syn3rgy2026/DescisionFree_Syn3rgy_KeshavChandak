"""
code_runner_tool.py
-------------------
Execute code files (Python, Node, etc.), capture stdout/stderr/exit code,
and format errors for debugging. Supports running tests too.
"""

import os
import subprocess
from smolagents import tool


def _run(cmd: str, cwd: str = None, timeout: int = 60) -> dict:
    """Run a command and return structured output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd or os.getcwd(),
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": f"TIMEOUT after {timeout}s"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}


def _format_result(r: dict) -> str:
    """Format result dict into a readable string."""
    parts = []
    if r["exit_code"] == 0:
        parts.append("✅ SUCCESS (exit code 0)")
    else:
        parts.append(f"❌ FAILED (exit code {r['exit_code']})")
    if r["stdout"]:
        parts.append(f"--- stdout ---\n{r['stdout'][:3000]}")
    if r["stderr"]:
        parts.append(f"--- stderr ---\n{r['stderr'][:3000]}")
    return "\n".join(parts)


@tool
def run_code(file_path: str, args: str = "") -> str:
    """Execute a code file and return stdout, stderr, and exit code.
    Automatically detects language by extension. Use this to run code you wrote,
    check for errors, and debug. Supports Python, Node.js, bash, and more.

    Args:
        file_path: Path to the code file to execute (e.g. 'output/app.py', 'output/index.js').
        args: Optional command-line arguments to pass (e.g. '--port 3000').

    Returns:
        str: Formatted output with exit code, stdout, stderr.
    """
    if not os.path.exists(file_path):
        return f"ERROR: File not found: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    runners = {
        ".py": "python3",
        ".js": "node",
        ".ts": "npx ts-node",
        ".sh": "bash",
        ".rb": "ruby",
        ".go": "go run",
    }

    runner = runners.get(ext)
    if not runner:
        return f"ERROR: Unsupported file extension '{ext}'. Supported: {', '.join(runners.keys())}"

    cmd = f"{runner} {file_path}"
    if args:
        cmd += f" {args}"

    return _format_result(_run(cmd))


@tool
def run_tests(command: str, project_dir: str = ".") -> str:
    """Run a test command (pytest, npm test, jest, etc.) and return results.
    Use this after writing code to verify it works correctly.

    Args:
        command: The test command to run (e.g. 'pytest tests/', 'npm test', 'jest --verbose').
        project_dir: Directory to run the command in. Defaults to current directory.

    Returns:
        str: Full test output with pass/fail status.
    """
    r = _run(command, cwd=project_dir, timeout=120)
    return _format_result(r)


@tool
def run_lint(file_path: str) -> str:
    """Run a linter on a code file to check for syntax errors and style issues.
    Auto-detects the right linter by file extension.

    Args:
        file_path: Path to the file to lint.

    Returns:
        str: Linter output — errors, warnings, or 'clean'.
    """
    if not os.path.exists(file_path):
        return f"ERROR: File not found: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    linters = {
        ".py": f"python3 -m py_compile {file_path}",
        ".js": f"npx eslint {file_path} --no-eslintrc 2>&1 || node --check {file_path}",
        ".ts": f"npx tsc --noEmit {file_path}",
        ".json": f"python3 -c \"import json; json.load(open('{file_path}'))\"",
    }

    linter_cmd = linters.get(ext)
    if not linter_cmd:
        return f"No linter configured for '{ext}'. Try running the file with run_code instead."

    r = _run(linter_cmd)
    if r["exit_code"] == 0:
        return f"✅ No syntax errors in {file_path}"
    return _format_result(r)


CODE_RUNNER_TOOLS = [
    run_code,
    run_tests,
    run_lint,
]
