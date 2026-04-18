# OWNER: Person 2
"""
shell_tool.py
-------------
Executes shell commands in a controlled subprocess with a configurable
timeout (config.SHELL_TIMEOUT). Always requests human confirmation before
running any destructive command (rm/del, sudo, etc.).

Exposes two smolagents @tool functions:
  - run_command      : general runner with automatic danger detection
  - run_safe_command : fast path for pre-approved safe commands

Cross-platform: covers both Unix (rm, ls, pwd, cat, which) and
Windows (del, rd, rmdir, dir, cd, type, where) equivalents.
"""

import sys
import subprocess
import config
from smolagents import tool

# Importing the human confirmation tool you (Person 2) are also building
from tools.human_confirm import ask_human_confirmation


# ---------------------------------------------------------------------------
# Internal helpers — NOT exported as tools
# ---------------------------------------------------------------------------

def is_destructive(command: str) -> bool:
    """
    Heuristically determine whether a command is potentially destructive.
    Covers both Unix/Linux and Windows command equivalents.

    Args:
        command (str): Command string to inspect.

    Returns:
        bool: True if the command should be flagged for confirmation.
    """
    risky_keywords = [
        "pip install",
        # Unix sensitive paths
        "/etc/", "/sys/", "/usr/",
        # Cross-platform dangerous ops
        "format", "shutdown",
    ]

    stripped = command.strip()
    padded = f" {stripped} "

    # Unix: rm / sudo
    if " rm " in padded or stripped.startswith("rm "):
        return True
    if " sudo " in padded or stripped.startswith("sudo "):
        return True

    # Windows: del, rd, rmdir
    if " del " in padded or stripped.startswith("del "):
        return True
    if stripped.startswith("rd ") or stripped.startswith("rmdir "):
        return True

    for keyword in risky_keywords:
        if keyword in command:
            return True

    return False


def _execute_subprocess(command: str) -> str:
    """
    Low-level subprocess runner. Returns combined stdout + stderr as a string.
    Called by the public @tool functions after confirmation is handled.

    Args:
        command (str): Shell command to run.

    Returns:
        str: Command output (stdout + stderr combined), or a timeout/error message.
    """
    timeout_limit = getattr(config, "SHELL_TIMEOUT", 30)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_limit,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output.strip() or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout_limit} seconds."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# ---------------------------------------------------------------------------
# Safe-command allow-list (used by run_safe_command)
# ---------------------------------------------------------------------------

SAFE_PREFIXES = [
    # Cross-platform
    "echo", "mkdir", "whoami", "git status", "python --version", "pip list",
    # Unix / Linux / Mac
    "ls", "pwd", "cat", "which",
    # Windows equivalents
    "dir",    # → ls
    "cd",     # → pwd  (also valid on Unix)
    "type",   # → cat
    "where",  # → which
]


# ---------------------------------------------------------------------------
# Public smolagents @tool functions
# ---------------------------------------------------------------------------

@tool
def run_command(command: str) -> str:
    """Run a shell command and return its output. Automatically asks for human
    confirmation before executing any risky or destructive command (those
    containing rm, del, sudo, rd, rmdir, pip install, format, shutdown, or
    sensitive Unix paths like /etc/, /sys/, /usr/).

    Args:
        command: The shell command string to execute.

    Returns:
        str: Combined stdout and stderr output, or a cancellation / error message.
    """
    if is_destructive(command):
        response = ask_human_confirmation(
            action=f"Run shell command: `{command}`",
            reason="This command was flagged as potentially destructive or touches sensitive system directories.",
            risk_level="HIGH",
        )
        if response.strip().upper() != "YES":
            return f"Execution cancelled by user. (Response: '{response}')"

    return _execute_subprocess(command)


@tool
def run_safe_command(command: str) -> str:
    """Run a pre-approved safe command without a confirmation prompt.
    Safe list (Unix): ls, pwd, cat, which, echo, mkdir, whoami, git status,
    python --version, pip list.
    Safe list (Windows): dir, cd, type, where, echo, mkdir, whoami, git status,
    python --version, pip list.
    If the command is NOT on the safe list it is handed off to run_command,
    which will ask for confirmation if needed.

    Args:
        command: The shell command string to execute.

    Returns:
        str: Combined stdout and stderr output.
    """
    stripped = command.strip()

    for safe_prefix in SAFE_PREFIXES:
        if stripped == safe_prefix or stripped.startswith(safe_prefix + " "):
            return _execute_subprocess(command)

    # Not in the safe list — delegate to run_command (handles confirmation)
    return run_command(command)


# ---------------------------------------------------------------------------
# TEST BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    IS_WINDOWS = sys.platform == "win32"

    print("\n" + "=" * 40)
    print("TESTING SHELL TOOL")
    print("=" * 40 + "\n")

    # Test 1: Print current directory — cross-platform
    dir_cmd = "cd" if IS_WINDOWS else "pwd"
    print(f"--- Test 1: Safe Command ({dir_cmd}) ---")
    print(run_safe_command(dir_cmd))
    print("-" * 40 + "\n")

    # Test 2: Echo — works on both platforms
    print("--- Test 2: Safe Command (echo) ---")
    print(run_safe_command("echo hello world"))
    print("-" * 40 + "\n")

    # Test 3: Risky delete — MUST trigger the confirmation prompt
    risky_cmd = "del C:\\nonexistent_dummy.txt" if IS_WINDOWS else "rm /tmp/dummy_test_file.txt"
    print(f"--- Test 3: Risky Command ({risky_cmd.split()[0]}) ---")
    print("Expected: You should be prompted to confirm before anything runs.")
    print(run_safe_command(risky_cmd))
    print("-" * 40 + "\n")

    print("Testing complete. If Test 3 paused and asked for confirmation, you are good to go!")