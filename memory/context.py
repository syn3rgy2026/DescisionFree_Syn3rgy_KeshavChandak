"""
context.py
----------
AgentContextManager — manages a rolling context window for the agent.

NOT a smolagents Tool. This is a utility class wired into core_agent.py
that keeps a full history of steps, auto-compresses old steps into a
rolling summary when history exceeds a threshold, and provides a clean
string for the agent's system prompt.
"""


class AgentContextManager:
    """
    Maintains agent step history with automatic compression.

    - Keeps the last `recent_window` steps in full detail.
    - When total history exceeds `compress_threshold`, steps older than
      the recent window are compressed into a rolling summary by calling
      a provided summarise function (typically an LLM call).
    """

    def __init__(self, recent_window: int = 6, compress_threshold: int = 10):
        self.recent_window = recent_window
        self.compress_threshold = compress_threshold
        self.history: list[dict] = []
        self.active_context: list[str] = []
        self._rolling_summary: str = ""

    def add_step(self, step_number: int, thought: str, action: str, observation: str):
        """Record a completed agent step."""
        try:
            self.history.append({
                "step": step_number,
                "thought": thought or "",
                "action": action or "",
                "observation": observation or "",
            })
        except Exception:
            pass

    def add_context(self, item: str):
        """Add an item to the active context list (e.g. 'user prefers markdown')."""
        try:
            if item and item not in self.active_context:
                self.active_context.append(item)
        except Exception:
            pass

    def needs_compression(self) -> bool:
        """Return True when history is long enough to trigger compression."""
        try:
            return len(self.history) > self.compress_threshold
        except Exception:
            return False

    def compress(self, summarise_fn=None):
        """
        Compress older steps into a rolling summary.

        Args:
            summarise_fn: Callable that takes a string of old steps and
                          returns a compressed summary string.
                          If None, a simple concatenation is used.
        """
        try:
            if len(self.history) <= self.recent_window:
                return

            old_steps = self.history[:-self.recent_window]
            self.history = self.history[-self.recent_window:]

            old_text_parts = []
            for s in old_steps:
                old_text_parts.append(
                    f"Step {s['step']}: {s['thought'][:120]} → {s['observation'][:120]}"
                )
            old_text = "\n".join(old_text_parts)

            if summarise_fn:
                try:
                    new_summary = summarise_fn(
                        f"Compress these agent steps into a brief rolling summary "
                        f"(max 200 words). Preserve key facts, file paths, and decisions.\n\n"
                        f"Previous summary:\n{self._rolling_summary}\n\n"
                        f"New steps to compress:\n{old_text}"
                    )
                    self._rolling_summary = str(new_summary).strip()
                except Exception:
                    self._rolling_summary += "\n" + old_text
            else:
                self._rolling_summary += "\n" + old_text

        except Exception:
            pass

    def get_context_for_prompt(self) -> str:
        """
        Return a formatted string combining:
          1. Rolling summary of compressed older steps
          2. Recent step history in full
          3. Active context items

        This string is appended to the system prompt so the agent
        remembers what it has done so far.
        """
        try:
            parts = []

            if self._rolling_summary.strip():
                parts.append(
                    "## Previous Steps (compressed summary)\n"
                    + self._rolling_summary.strip()
                )

            if self.history:
                recent_lines = []
                for s in self.history:
                    recent_lines.append(
                        f"- **Step {s['step']}**: {s['thought'][:200]}\n"
                        f"  Action: {s['action'][:200]}\n"
                        f"  Result: {s['observation'][:200]}"
                    )
                parts.append(
                    "## Recent Steps\n" + "\n".join(recent_lines)
                )

            if self.active_context:
                ctx_lines = [f"- {c}" for c in self.active_context]
                parts.append(
                    "## Active Context\n" + "\n".join(ctx_lines)
                )

            if not parts:
                return ""

            return "\n\n".join(parts)

        except Exception:
            return ""

    def clear(self):
        """Reset all context state."""
        try:
            self.history.clear()
            self.active_context.clear()
            self._rolling_summary = ""
        except Exception:
            pass
