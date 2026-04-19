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
import re
import sqlite3
import hashlib
import threading
DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "memory.db")

_db_lock = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the memory database, creating tables if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    # Deduped lessons from code-action / parsing format failures (smolagents, etc.)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS formatting_lessons (
            signature  TEXT PRIMARY KEY,
            lesson     TEXT NOT NULL,
            hit_count  INTEGER NOT NULL DEFAULT 1,
            last_seen  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _format_error_signature(raw: str) -> str:
    """Stable hash so near-duplicate parser errors collapse to one lesson."""
    norm = re.sub(r"\s+", " ", (raw or "").strip().lower())[:800]
    return hashlib.sha256(norm.encode("utf-8", errors="replace")).hexdigest()


class MemoryManager:
    """Manages reading and writing of task history and user memory."""

    def __init__(self):
        """Initialize and ensure DB tables exist."""
        self.conn = _get_connection()

    def record_formatting_lesson(self, raw_error: str, task_hint: str = "") -> None:
        """
        Persist a code-action / parser formatting failure so future system prompts
        include it (deduped by error signature).
        """
        raw = (raw_error or "").strip()
        if not raw:
            return
        sig = _format_error_signature(raw)
        hint = (task_hint or "").replace("\n", " ").strip()[:200]
        lesson = (
            "Required: use the exact Thought / Action / code block structure the runtime expects; "
            "do not merge steps or skip delimiters. "
            f"Previous parser failure{f' (task: {hint})' if hint else ''}: {raw[:450]}"
        )
        try:
            with _db_lock:
                self.conn.execute(
                    """
                    INSERT INTO formatting_lessons (signature, lesson, hit_count, last_seen)
                    VALUES (?, ?, 1, datetime('now'))
                    ON CONFLICT(signature) DO UPDATE SET
                        hit_count = hit_count + 1,
                        last_seen = datetime('now')
                    """,
                    (sig, lesson),
                )
                self.conn.commit()
        except Exception as e:
            print(f"⚠️  Failed to record formatting lesson: {e}")

    def get_formatting_lessons(self, n: int = 8) -> list[str]:
        """Lines to inject into memory context (most recent first)."""
        try:
            with _db_lock:
                rows = self.conn.execute(
                    """
                    SELECT lesson, hit_count, last_seen FROM formatting_lessons
                    ORDER BY last_seen DESC LIMIT ?
                    """,
                    (n,),
                ).fetchall()
            out = []
            for lesson, hits, seen in rows:
                line = f"- (×{hits}, {seen}) {lesson}"
                out.append(line[:700])
            return out
        except Exception:
            return []

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
            with _db_lock:
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
            with _db_lock:
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
            with _db_lock:
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
            with _db_lock:
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
        0. Formatting / code-action parser lessons from past runs
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

        format_lines = self.get_formatting_lessons(8)
        if format_lines:
            sections.append(
                "## Code action format — learn from past parser failures\n"
                "These errors already happened on this machine. Match the agent's expected "
                "Thought/Action/code structure; do not repeat patterns that triggered them.\n\n"
                + "\n".join(format_lines)
            )

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

        # 3. Scan actual files on disk so the agent knows what exists
        # This is the KEY fix — the agent couldn't find research files before
        try:
            import glob
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scan_dirs = [project_root, os.path.join(project_root, "output")]
            extensions = ["*.md", "*.txt", "*.py", "*.html", "*.csv", "*.json", "*.docx", "*.pptx"]
            found_files = []

            for scan_dir in scan_dirs:
                if not os.path.isdir(scan_dir):
                    continue
                for ext in extensions:
                    for f in glob.glob(os.path.join(scan_dir, ext)):
                        basename = os.path.basename(f)
                        # Skip hidden files and common config
                        if basename.startswith(".") or basename in ("config.py", "main.py", "requirements.txt"):
                            continue
                        rel = os.path.relpath(f, project_root)
                        size = os.path.getsize(f)
                        if size > 0:
                            found_files.append(f"- `{rel}` ({size} bytes)")

            # Also scan output/ subdirectories one level deep
            output_dir = os.path.join(project_root, "output")
            if os.path.isdir(output_dir):
                for subdir in os.listdir(output_dir):
                    subpath = os.path.join(output_dir, subdir)
                    if os.path.isdir(subpath):
                        for ext in extensions:
                            for f in glob.glob(os.path.join(subpath, ext)):
                                basename = os.path.basename(f)
                                if not basename.startswith("."):
                                    rel = os.path.relpath(f, project_root)
                                    size = os.path.getsize(f)
                                    if size > 0:
                                        found_files.append(f"- `{rel}` ({size} bytes)")

            if found_files:
                sections.append(
                    "## Files Available on Disk\n"
                    "These files exist in the project. You can read them with `read_file`.\n\n"
                    + "\n".join(found_files[:20])  # cap at 20 to avoid bloat
                )
        except Exception:
            pass

        # 4. User facts from persistent memory
        try:
            with _db_lock:
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
            with _db_lock:
                self.conn.execute("DELETE FROM task_history")
                self.conn.commit()
        except Exception as e:
            print(f"⚠️  Failed to clear task log: {e}")


_memory_manager_singleton: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Process-wide singleton so UI + agent share one DB handle (thread-safe via lock)."""
    global _memory_manager_singleton
    if _memory_manager_singleton is None:
        with _db_lock:
            if _memory_manager_singleton is None:
                _memory_manager_singleton = MemoryManager()
    return _memory_manager_singleton
