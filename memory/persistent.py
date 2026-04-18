"""
persistent.py
-------------
Long-term persistent memory backed by SQLite.
Stores facts, file paths, user preferences, and configuration
across sessions at ~/.agent/memory.db.
"""

import os
import sqlite3
from smolagents import Tool


DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "memory.db")


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the memory database, creating it if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            key       TEXT PRIMARY KEY,
            value     TEXT NOT NULL,
            category  TEXT NOT NULL DEFAULT 'fact',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


class PersistentMemoryTool(Tool):
    name = "persistent_memory"
    description = """Use this tool to store and retrieve information that must survive across sessions.
Good for: user preferences, important facts the user told you, file paths worth
remembering, configuration values, or anything the user says to "remember".

Categories: fact, path, preference, config.

Supported actions:
  set    — store a key-value pair with a category  (requires key + value, optional category)
  get    — retrieve a value by key                  (requires key)
  list   — show all stored memories                 (optional category to filter)
  search — find memories whose key or value contains a substring (requires value as query)
  delete — remove a memory by key                   (requires key)
"""
    inputs = {
        "action": {
            "type": "string",
            "description": "One of: set, get, list, search, delete",
        },
        "key": {
            "type": "string",
            "description": "The memory key (required for set/get/delete)",
            "nullable": True,
        },
        "value": {
            "type": "string",
            "description": "The value to store, or the search query string",
            "nullable": True,
        },
        "category": {
            "type": "string",
            "description": "One of: fact, path, preference, config. Defaults to 'fact'",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(
        self,
        action: str,
        key: str = None,
        value: str = None,
        category: str = None,
    ) -> str:
        try:
            action = action.strip().lower()
            cat = (category or "fact").strip().lower()

            if action == "set":
                if not key:
                    return "ERROR: 'set' requires a key"
                if value is None:
                    return "ERROR: 'set' requires a value"
                try:
                    conn = _get_connection()
                    conn.execute(
                        "INSERT OR REPLACE INTO memories (key, value, category) VALUES (?, ?, ?)",
                        (key, value, cat),
                    )
                    conn.commit()
                    conn.close()
                except Exception as e:
                    return f"ERROR: database write failed — {str(e)}"
                return f"OK — remembered '{key}' [{cat}]"

            elif action == "get":
                if not key:
                    return "ERROR: 'get' requires a key"
                try:
                    conn = _get_connection()
                    row = conn.execute(
                        "SELECT value, category FROM memories WHERE key = ?", (key,)
                    ).fetchone()
                    conn.close()
                except Exception as e:
                    return f"ERROR: database read failed — {str(e)}"
                if not row:
                    return f"NOT_FOUND — no memory for '{key}'"
                return f"[{row[1]}] {row[0]}"

            elif action == "list":
                try:
                    conn = _get_connection()
                    if category:
                        rows = conn.execute(
                            "SELECT key, value, category FROM memories WHERE category = ? ORDER BY timestamp DESC",
                            (cat,),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            "SELECT key, value, category FROM memories ORDER BY timestamp DESC"
                        ).fetchall()
                    conn.close()
                except Exception as e:
                    return f"ERROR: database read failed — {str(e)}"
                if not rows:
                    return "(no memories stored)"
                lines = [f"  [{r[2]}] {r[0]}: {r[1]}" for r in rows]
                return "Persistent Memories:\n" + "\n".join(lines)

            elif action == "search":
                if not value:
                    return "ERROR: 'search' requires a value (the query string)"
                try:
                    conn = _get_connection()
                    query = f"%{value}%"
                    rows = conn.execute(
                        "SELECT key, value, category FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY timestamp DESC",
                        (query, query),
                    ).fetchall()
                    conn.close()
                except Exception as e:
                    return f"ERROR: database search failed — {str(e)}"
                if not rows:
                    return f"No memories matching '{value}'"
                lines = [f"  [{r[2]}] {r[0]}: {r[1]}" for r in rows]
                return f"Search results for '{value}':\n" + "\n".join(lines)

            elif action == "delete":
                if not key:
                    return "ERROR: 'delete' requires a key"
                try:
                    conn = _get_connection()
                    cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
                    conn.commit()
                    deleted = cursor.rowcount
                    conn.close()
                except Exception as e:
                    return f"ERROR: database delete failed — {str(e)}"
                if deleted == 0:
                    return f"NOT_FOUND — no memory for '{key}'"
                return f"OK — deleted '{key}'"

            else:
                return f"ERROR: unknown action '{action}'. Use set/get/list/search/delete"

        except Exception as e:
            return f"ERROR: {str(e)}"
