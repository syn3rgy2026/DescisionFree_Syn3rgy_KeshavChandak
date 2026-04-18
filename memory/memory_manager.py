"""
memory_manager.py
-----------------
Manages persistent memory for Synergy Agent across sessions.

Responsibilities:
- Auto-save task results + errors after every task
- Load relevant past context before each new task
- Store and recall user facts (name, preferences, etc.)
- Maintain a task log for the agent to learn from mistakes
"""

import os
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "memory.db")


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the memory database, creating tables if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Existing memories table (used by persistent_memory tool)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            key       TEXT PRIMARY KEY,
            value     TEXT NOT NULL,
            category  TEXT NOT NULL DEFAULT 'fact',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # New task_history table — auto-populated after each task
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            task      TEXT NOT NULL,
            result    TEXT NOT NULL,
            status    TEXT NOT NULL DEFAULT 'completed',
            errors    TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


class MemoryManager:
    """Manages reading and writing of task history and user memory."""

    def __init__(self):
        """Initialize and ensure DB tables exist."""
        self.conn = _get_connection()

    def log_task(self, task: str, result: str, status: str = "completed", errors: str = "") -> None:
        """
        Save a completed task and its result to the task history.

        This is called automatically after every agent run so the agent
        can learn from past successes and mistakes.

        Args:
            task: The original user task string.
            result: The agent's final result/output.
            status: 'completed', 'failed', or 'error'.
            errors: Any error messages encountered during the task.
        """
        try:
            self.conn.execute(
                "INSERT INTO task_history (task, result, status, errors) VALUES (?, ?, ?, ?)",
                (task, str(result)[:5000], status, str(errors)[:2000]),
            )
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Failed to log task: {e}")

    def get_recent_history(self, n: int = 5) -> list[dict]:
        """
        Return the n most recent task log entries.

        Args:
            n: Number of entries to retrieve.

        Returns:
            list[dict]: Each dict has keys 'task', 'result', 'status', 'errors', 'timestamp'.
        """
        try:
            rows = self.conn.execute(
                "SELECT task, result, status, errors, timestamp FROM task_history ORDER BY id DESC LIMIT ?",
                (n,),
            ).fetchall()
            return [
                {"task": r[0], "result": r[1], "status": r[2], "errors": r[3], "timestamp": r[4]}
                for r in rows
            ]
        except Exception:
            return []

    def get_failed_tasks(self, n: int = 5) -> list[dict]:
        """
        Return the n most recent FAILED tasks — so the agent can avoid repeating mistakes.

        Args:
            n: Number of failed entries to retrieve.

        Returns:
            list[dict]: Failed task entries.
        """
        try:
            rows = self.conn.execute(
                "SELECT task, result, status, errors, timestamp FROM task_history "
                "WHERE status != 'completed' ORDER BY id DESC LIMIT ?",
                (n,),
            ).fetchall()
            return [
                {"task": r[0], "result": r[1], "status": r[2], "errors": r[3], "timestamp": r[4]}
                for r in rows
            ]
        except Exception:
            return []

    def search_history(self, query: str, n: int = 5) -> list[dict]:
        """
        Search task history for tasks similar to a query.

        Args:
            query: Search string to match against task descriptions.
            n: Max results.

        Returns:
            list[dict]: Matching task history entries.
        """
        try:
            rows = self.conn.execute(
                "SELECT task, result, status, errors, timestamp FROM task_history "
                "WHERE task LIKE ? OR result LIKE ? OR errors LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", f"%{query}%", n),
            ).fetchall()
            return [
                {"task": r[0], "result": r[1], "status": r[2], "errors": r[3], "timestamp": r[4]}
                for r in rows
            ]
        except Exception:
            return []

    def build_memory_context(self, task: str) -> str:
        """
        Build a context string to inject into the system prompt before a task.

        This loads:
        1. Recent task history (so the agent knows what it did before)
        2. Past failures (so it doesn't repeat mistakes)
        3. Relevant past tasks (keyword match against the new task)
        4. Stored user facts from persistent memory

        Args:
            task: The new task the user is about to run.

        Returns:
            str: A formatted context block to prepend to the system prompt.
        """
        sections = []

        # 1. Recent history (last 3 tasks)
        recent = self.get_recent_history(3)
        if recent:
            lines = []
            for entry in recent:
                status_icon = "✅" if entry["status"] == "completed" else "❌"
                result_preview = entry["result"][:200]
                lines.append(
                    f"- {status_icon} **{entry['task'][:100]}** → {result_preview}"
                )
                if entry["errors"]:
                    lines.append(f"  ⚠️ Error: {entry['errors'][:150]}")
            sections.append(
                "## Recent Task History\n"
                "You completed these tasks recently. Use this context to avoid repeating work.\n\n"
                + "\n".join(lines)
            )

        # 2. Past failures — critical for learning
        failures = self.get_failed_tasks(3)
        if failures:
            lines = []
            for entry in failures:
                lines.append(
                    f"- ❌ **{entry['task'][:100]}**\n"
                    f"  Error: {entry['errors'][:200]}\n"
                    f"  Result: {entry['result'][:200]}"
                )
            sections.append(
                "## ⚠️ Past Failures — DO NOT REPEAT THESE MISTAKES\n"
                "These tasks failed before. If the current task is similar, use a DIFFERENT approach.\n\n"
                + "\n".join(lines)
            )

        # 3. Search for tasks related to the current one
        # Extract key words from the task
        keywords = [w for w in task.lower().split() if len(w) > 3][:5]
        related_seen = set()
        for kw in keywords:
            related = self.search_history(kw, 2)
            for entry in related:
                key = entry["task"][:50]
                if key not in related_seen:
                    related_seen.add(key)

        # 4. User facts from persistent memory
        try:
            rows = self.conn.execute(
                "SELECT key, value, category FROM memories ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
            if rows:
                lines = [f"- [{r[2]}] {r[0]}: {r[1]}" for r in rows]
                sections.append(
                    "## Stored User Facts & Preferences\n"
                    + "\n".join(lines)
                )
        except Exception:
            pass

        if not sections:
            return ""

        return "\n\n---\n\n".join(sections)

    def clear_task_log(self) -> None:
        """Erase all entries from task history."""
        try:
            self.conn.execute("DELETE FROM task_history")
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Failed to clear task log: {e}")
