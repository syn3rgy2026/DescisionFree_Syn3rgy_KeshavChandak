# OWNER: Person 2
"""
shell_tool.py
-------------
Executes shell commands in a controlled subprocess with a configurable
timeout (config.SHELL_TIMEOUT). Always requests human confirmation before
running any destructive command (rm, sudo, etc.).
"""

import subprocess
import config


def run_command(command: str, require_confirm: bool = False) -> dict:
    """
    Execute a shell command and return its stdout, stderr, and exit code.

    Args:
        command (str): Shell command string to execute.
        require_confirm (bool): If True, prompt the user for confirmation first.

    Returns:
        dict: Keys 'stdout', 'stderr', 'returncode'.
    """
    raise NotImplementedError("Person 2 will implement this")


def is_destructive(command: str) -> bool:
    """
    Heuristically determine whether a command is potentially destructive.

    Args:
        command (str): Command string to inspect.

    Returns:
        bool: True if the command should be flagged for confirmation.
    """
    raise NotImplementedError("Person 2 will implement this")


def safe_run(command: str) -> dict:
    """
    Run a command, automatically requiring confirmation if it looks destructive.

    Args:
        command (str): Shell command string.

    Returns:
        dict: Same structure as run_command return value.
    """
    raise NotImplementedError("Person 2 will implement this")
