"""
error_recovery.py
-----------------
Wraps the agent runner with retry logic, error augmentation,
and optional user-driven rephrasing.
"""

import time
import traceback
from rich.console import Console

console = Console()


def run_with_recovery(run_fn, task: str, max_attempts: int = 3):
    """
    Try to execute a task up to *max_attempts* times with smart recovery.

    On each failure the task is augmented with error context so the agent
    avoids repeating the same mistake.  After all retries are exhausted
    the user is offered the chance to rephrase.

    Args:
        run_fn:       Callable that takes a task string and returns a result.
                      Typically this is ``run_agent`` from core_agent.
        task:         The original user task string.
        max_attempts: How many tries before asking the user (default 3).

    Returns:
        tuple: (result_or_summary: str, success: bool)
    """
    last_error = None
    current_task = task

    for attempt in range(1, max_attempts + 1):
        # We no longer print raw "Attempt X/Y" here because it's now 
        # rendered inside the TUI Dashboard header by run_agent.

        try:
            # Pass the attempt number to run_fn (run_agent)
            result = run_fn(current_task, attempt=attempt)
            return result, True

        except Exception as exc:
            last_error = exc
            error_msg = str(exc)
            
            # Silent logging or dim logging to avoid breaking dashboard flow
            if attempt < max_attempts:
                # Augment the task so the agent learns from the failure
                current_task = (
                    f"{task}\n\n"
                    f"--- IMPORTANT: PREVIOUS ATTEMPT FAILED ---\n"
                    f"Error: {error_msg}\n"
                    f"Do NOT use the same approach that caused this error. "
                    f"Try a completely different strategy.\n"
                    f"-------------------------------------------"
                )

    # ── All attempts exhausted — ask the user ────────────────────────
    # Use high-contrast prompt for the recovery question
    while True:
        choice = console.input(
            "\n[bold yellow]⚠️ All 3 attempts failed. Rephrase task? (yes/no): [/bold yellow]"
        ).strip().lower()

        if choice in ("yes", "y"):
            new_task = console.input("[bold cyan]Enter new task: [/bold cyan]").strip()
            if new_task:
                return run_with_recovery(run_fn, new_task, max_attempts)
        elif choice in ("no", "n"):
            summary = f"Task failed after {max_attempts} attempts. Last error: {last_error}"
            return summary, False


# ── Self-test: simulate failures and recovery ────────────────────────
if __name__ == "__main__":
    call_count = 0

    def fake_run_agent(task: str) -> str:
        """Fails twice then succeeds on the third try."""
        global call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError(f"Simulated failure #{call_count}")
        return "✅ Simulated success on attempt 3"

    console.print("\n[bold magenta]═══ Test: Fails twice, succeeds on third ═══[/bold magenta]\n")
    result, success = run_with_recovery(fake_run_agent, "do something tricky")
    console.print(f"\nResult : {result}")
    console.print(f"Success: {success}")

    # Reset for second test
    call_count = 0

    def always_fail(task: str) -> str:
        """Always fails."""
        global call_count
        call_count += 1
        raise RuntimeError(f"Permanent failure #{call_count}")

    console.print("\n[bold magenta]═══ Test: Always fails (will ask to rephrase) ═══[/bold magenta]\n")
    result2, success2 = run_with_recovery(always_fail, "impossible task")
    console.print(f"\nResult : {result2}")
    console.print(f"Success: {success2}")
