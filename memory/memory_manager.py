# OWNER: Person 4
"""
memory_manager.py
-----------------
Manages persistent memory for Synergy Agent across sessions.

Responsibilities:
- Load and save user facts/preferences to memory/user_memory.md
- Append task summaries and outcomes to memory/task_log.md
- Provide a simple key-value interface for the agent to read/write user facts
- Summarise recent task history for injection into the system prompt
"""

import os
import config


class MemoryManager:
    """Handles reading and writing of user memory and task logs."""

    def __init__(self):
        """Initialise paths and load existing memory into internal state."""
        raise NotImplementedError("Person 4 will implement this")

    def load_user_memory(self) -> dict:
        """
        Parse user_memory.md and return a dict of stored user facts.

        Returns:
            dict: Key-value pairs of user preferences and facts.
        """
        raise NotImplementedError("Person 4 will implement this")

    def save_user_memory(self, key: str, value: str) -> None:
        """
        Persist a new or updated user fact to user_memory.md.

        Args:
            key (str): Fact identifier (e.g. 'preferred_language').
            value (str): Value to store.
        """
        raise NotImplementedError("Person 4 will implement this")

    def log_task(self, task: str, result: str, status: str = "completed") -> None:
        """
        Append a task entry to task_log.md.

        Args:
            task (str): The original user task string.
            result (str): Summary of what the agent produced.
            status (str): Outcome status ('completed', 'failed', 'aborted').
        """
        raise NotImplementedError("Person 4 will implement this")

    def get_recent_history(self, n: int = 5) -> list:
        """
        Return the n most recent task log entries.

        Args:
            n (int): Number of entries to retrieve.

        Returns:
            list[dict]: Each dict has keys 'task', 'result', 'status', 'timestamp'.
        """
        raise NotImplementedError("Person 4 will implement this")

    def clear_task_log(self) -> None:
        """Erase all entries from task_log.md."""
        raise NotImplementedError("Person 4 will implement this")
