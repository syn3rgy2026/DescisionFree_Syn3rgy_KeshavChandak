# OWNER: Person 2
"""
human_confirm.py
----------------
Interrupts the agentic loop to request explicit human approval before
the agent takes a sensitive or irreversible action (e.g. running a
destructive shell command, sending an email, deleting files).

Uses rich for a clearly-formatted confirmation prompt.

TUI-aware: when the Textual TUI is active, the prompt is routed to the
TUI input bar instead of stdin (which Textual has captured).

Public API (smolagents @tool):
    ask_human_confirmation(action, reason, risk_level, details="")
"""

import json
import threading
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from smolagents import tool

console = Console()

# ── TUI bridge ────────────────────────────────────────────────────────
# When the Textual app is running it sets _tui_app to itself.
# The worker thread calling ask_human_confirmation checks this and,
# if set, posts the confirmation prompt to the TUI input bar instead
# of trying Prompt.ask (which would block forever).

_tui_app = None          # set by ui/app.py on_mount, cleared on exit
_tui_response = None     # str: the user's response text
_tui_event = threading.Event()  # signalled when the user responds


def set_tui_app(app):
    """Called by Textual app on mount to enable TUI-mode prompts."""
    global _tui_app
    _tui_app = app


def clear_tui_app():
    """Called by Textual app on exit to disable TUI-mode prompts."""
    global _tui_app
    _tui_app = None


def _submit_tui_response(response: str):
    """Called by the Textual app when the user types an answer."""
    global _tui_response
    _tui_response = response
    _tui_event.set()


def _ask_via_tui(message: str) -> str:
    """Block the worker thread until the user answers in the TUI."""
    global _tui_response
    _tui_event.clear()
    _tui_response = None
    # Post the confirmation request to the TUI event loop
    _tui_app.call_from_thread(_tui_app.request_human_confirmation, message)
    # Wait for the user to type a response (no timeout — the user decides)
    _tui_event.wait()
    return _tui_response or ""


@tool
def ask_human_confirmation(action: str, reason: str, risk_level: str, details: str = "") -> str:
    """Use this before doing anything that cannot be undone. This includes:
    deleting files, sending emails, submitting forms, running generated
    scripts, installing packages, any irreversible action. Returns the
    user's response as a string: 'YES' to allow, 'NO' to cancel, or
    alternative instructions to follow instead.

    Args:
        action: What the agent wants to do.
        reason: Why it wants to do it.
        risk_level: Severity — LOW, MEDIUM, or HIGH.
        details: Optional JSON string of extra key-value context to display
                 (e.g. '{"File": "report.csv", "Size": "4 KB"}'). Leave
                 empty string if not needed.

    Returns:
        str: User's response — 'YES', 'NO', or custom instructions.
    """
    # Map risk level to a display color
    risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}.get(
        risk_level.upper(), "green"
    )

    # --- Build the confirmation text ---
    lines = [
        f"Action: {action}",
        f"Reason: {reason}",
        f"Risk:   {risk_level.upper()}",
    ]

    if details and details.strip():
        try:
            detail_dict = json.loads(details)
            for k, v in detail_dict.items():
                lines.append(f"  {k}: {v}")
        except json.JSONDecodeError:
            lines.append(f"Details: {details}")

    summary = "\n".join(lines)

    # ── TUI mode: route to Textual input bar ─────────────────────────
    if _tui_app is not None:
        return _ask_via_tui(summary)

    # ── CLI mode: original Rich prompt ───────────────────────────────
    content = (
        f"[bold white]Action:[/bold white] {action}\n"
        f"[bold white]Reason:[/bold white] {reason}\n"
        f"[bold white]Risk:[/bold white]   [{risk_color}]{risk_level.upper()}[/{risk_color}]"
    )

    if details and details.strip():
        try:
            detail_dict = json.loads(details)
            detail_lines = "\n".join(
                f"  [cyan]{k}:[/cyan] {v}" for k, v in detail_dict.items()
            )
            content += f"\n\n[bold white]Details:[/bold white]\n{detail_lines}"
        except json.JSONDecodeError:
            content += f"\n\n[bold white]Details:[/bold white] {details}"

    panel = Panel(
        content,
        title="[bold red]🛑 HUMAN CONFIRMATION REQUIRED 🛑[/bold red]",
        border_style=risk_color,
    )
    console.print(panel)
    console.print(
        "[dim]Type [bold green]YES[/bold green] to allow, "
        "[bold red]NO[/bold red] to cancel, or type "
        "[bold cyan]alternative instructions[/bold cyan].[/dim]"
    )

    # Return a string so smolagents can feed it back into the LLM context
    response = Prompt.ask("❯")
    return response


# ---------------------------------------------------------------------------
# TEST BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 40)
    print("TESTING HUMAN CONFIRM TOOL")
    print("=" * 40 + "\n")

    # Test 1: HIGH risk — no details
    console.print("[bold magenta]--- Test 1: HIGH risk, no details ---[/bold magenta]")
    r1 = ask_human_confirmation(
        action="Run shell command: `rm -rf /tmp/cache`",
        reason="Clearing old cache files to free up disk space.",
        risk_level="HIGH",
    )
    console.print(f"\n[System] You entered: '[bold cyan]{r1}[/bold cyan]'\n")

    # Test 2: MEDIUM risk — with details dict serialised as JSON
    console.print("[bold magenta]--- Test 2: MEDIUM risk, with details ---[/bold magenta]")
    r2 = ask_human_confirmation(
        action="Overwrite existing file",
        reason="New data is ready and the old file needs to be replaced.",
        risk_level="MEDIUM",
        details=json.dumps({"File": "output/report.csv", "Size": "12 KB", "Last modified": "2026-04-18"}),
    )
    console.print(f"\n[System] You entered: '[bold cyan]{r2}[/bold cyan]'\n")

    # Test 3: LOW risk — with plain-text details (tests the fallback path)
    console.print("[bold magenta]--- Test 3: LOW risk, plain-text details ---[/bold magenta]")
    r3 = ask_human_confirmation(
        action="Send summary email",
        reason="Task is complete and user requested a summary.",
        risk_level="LOW",
        details="Recipient: team@example.com",
    )
    console.print(f"\n[System] You entered: '[bold cyan]{r3}[/bold cyan]'\n")

    print("Testing complete!")