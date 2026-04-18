# OWNER: Person 2
"""
human_confirm.py
----------------
Interrupts the agentic loop to request explicit human approval before
the agent takes a sensitive or irreversible action (e.g. running a
destructive shell command, sending an email, deleting files).

Uses rich for a clearly-formatted confirmation prompt.
"""

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def ask(action_description: str) -> bool:
    """
    Display a confirmation prompt and return the user's yes/no decision.

    Args:
        action_description (str): Human-readable description of the action
                                  the agent wants to take.

    Returns:
        bool: True if the user approved, False otherwise.
    """
    raise NotImplementedError("Person 2 will implement this")


def ask_with_detail(action_description: str, details: dict) -> bool:
    """
    Show a detailed breakdown of an action before asking for confirmation.

    Args:
        action_description (str): Short description of the action.
        details (dict): Key-value pairs with extra context (e.g. command, path).

    Returns:
        bool: True if approved.
    """
    raise NotImplementedError("Person 2 will implement this")
