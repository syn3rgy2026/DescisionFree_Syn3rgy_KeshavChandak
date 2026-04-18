"""
working.py
----------
In-process working memory for the current agent session.
Uses a plain Python dict to store file paths, URLs, intermediate
variables, and scratchpad lists that the agent accumulates during
a single task execution.  All data is lost when the process exits.
"""

from smolagents import Tool


class WorkingMemoryTool(Tool):
    name = "working_memory"
    description = """Use this tool to store and retrieve temporary data DURING the current task.
Good for: saving file paths you created, URLs you found, intermediate variables,
or building up a list of items step-by-step.
Everything stored here is lost when the task ends — use persistent_memory for
data that must survive across sessions.

Supported actions:
  set    — store a key-value pair              (requires key + value)
  get    — retrieve a value by key             (requires key)
  append — append a value to a list under key  (requires key + value)
  list   — show all stored keys and values     (no extra args)
  clear  — wipe all working memory             (no extra args)
"""
    inputs = {
        "action": {
            "type": "string",
            "description": "One of: set, get, append, list, clear",
        },
        "key": {
            "type": "string",
            "description": "The memory key (required for set/get/append, ignored for list/clear)",
            "nullable": True,
        },
        "value": {
            "type": "string",
            "description": "The value to store or append (required for set/append)",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store: dict = {}

    def forward(self, action: str, key: str = None, value: str = None) -> str:
        try:
            action = action.strip().lower()

            if action == "set":
                if not key:
                    return "ERROR: 'set' requires a key"
                self._store[key] = value
                return f"OK — stored '{key}'"

            elif action == "get":
                if not key:
                    return "ERROR: 'get' requires a key"
                if key not in self._store:
                    return f"NOT_FOUND — no value for '{key}'"
                return str(self._store[key])

            elif action == "append":
                if not key:
                    return "ERROR: 'append' requires a key"
                if key not in self._store:
                    self._store[key] = []
                if not isinstance(self._store[key], list):
                    self._store[key] = [self._store[key]]
                self._store[key].append(value)
                return f"OK — appended to '{key}' (now {len(self._store[key])} items)"

            elif action == "list":
                if not self._store:
                    return "(working memory is empty)"
                lines = []
                for k, v in self._store.items():
                    lines.append(f"  {k}: {v}")
                return "Working Memory:\n" + "\n".join(lines)

            elif action == "clear":
                self._store.clear()
                return "OK — working memory cleared"

            else:
                return f"ERROR: unknown action '{action}'. Use set/get/append/list/clear"

        except Exception as e:
            return f"ERROR: {str(e)}"
