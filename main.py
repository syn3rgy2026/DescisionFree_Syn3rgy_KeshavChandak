"""
main.py
-------
CLI entry point for Synergy Agent.
Provides the interactive >>> loop, dispatches tasks to the agent,
and handles errors so the CLI never crashes.
"""

import sys
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from agent.core_agent import run_agent
from agent.error_recovery import run_with_recovery
from agent.skill_router import get_skills_for_task

console = Console()

# Messages cycled through during long agent runs (research-aware)
_THINKING_MESSAGES = [
    "Agent is thinking...",
    "Agent is reading a webpage...",
    "Agent is taking notes...",
    "Agent is searching the web...",
    "Agent is synthesising results...",
    "Agent is planning next steps...",
    "Agent is writing output...",
]


# ── Welcome Banner ────────────────────────────────────────────────────

def print_banner():
    """Display the startup banner."""
    banner = Panel(
        "[bold cyan]⚡ SYNERGY AGENT ⚡[/bold cyan]\n"
        "[dim]Autonomous AI Agent — SYN3RGY 3.0 Hackathon[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    )
    console.print(banner)


# ── Help / Commands Menu ─────────────────────────────────────────────

def print_help():
    """Show available commands and example tasks."""
    table = Table(
        title="Commands",
        border_style="blue",
        header_style="bold magenta",
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("[bold]help[/bold]",   "Show this menu again")
    table.add_row("[bold]exit[/bold]",   "Quit the agent cleanly")
    table.add_row("[bold]<task>[/bold]", "Describe any task for the agent to execute")

    console.print(table)

    console.print("\n[bold yellow]Example tasks:[/bold yellow]")
    console.print("  • Search the web for latest AI news and save a summary")
    console.print("  • Write a Python script that sorts a CSV by date")
    console.print("  • Create a PowerPoint presentation about climate change")
    console.print("  • Read data.json and generate a bar chart")
    console.print()


# ── Task Handler ─────────────────────────────────────────────────────

def _run_agent_in_thread(task: str, image, result_box: list):
    """Run the agent in a background thread and store (result, success) in result_box."""
    try:
        result, success = run_with_recovery(run_agent, task, image)
        result_box.append((result, success))
    except Exception as exc:
        result_box.append((str(exc), False))


def handle_task(task: str, image=None):
    """
    Run the agent with a live Rich spinner so the user always sees feedback.
    A background thread cycles through status messages every 8 seconds.
    """
    # Show which skills were detected — instant feedback
    skills_text = get_skills_for_task(task)
    detected = []
    if "research" in task.lower() or "investigate" in task.lower() or "analyze" in task.lower():
        detected.append("research_skill")
    if any(w in task.lower() for w in ["web", "search", "browse", "scrape"]):
        detected.append("web_skill")
    if any(w in task.lower() for w in ["ppt", "slide", "presentation"]):
        detected.append("ppt_skill")
    if any(w in task.lower() for w in ["code", "script", "python"]):
        detected.append("code_skill")

    console.print(Rule("[bold blue]Agent Starting[/bold blue]", style="blue"))

    if detected:
        console.print(f"[dim]📚 Skills loaded: {', '.join(detected)}[/dim]")

    # Run the agent in a background thread
    result_box: list = []
    agent_thread = threading.Thread(target=_run_agent_in_thread, args=(task, image, result_box), daemon=True)
    agent_thread.start()

    # Show a live spinner while the thread is running
    start_time = time.time()
    msg_index  = 0

    with Live(console=console, refresh_per_second=4, transient=True) as live:
        while agent_thread.is_alive():
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            time_str = f"{mins}m {secs}s" if mins else f"{secs}s"

            # Cycle status message every 8 seconds
            msg_index = (elapsed // 8) % len(_THINKING_MESSAGES)
            status_line = (
                f"[bold cyan]⟳[/bold cyan]  "
                f"[dim]{_THINKING_MESSAGES[msg_index]}[/dim]  "
                f"[dim italic]({time_str})[/dim italic]"
            )
            live.update(Text.from_markup(status_line))
            time.sleep(0.25)

    # Wait for thread to fully finish (should be done by now)
    agent_thread.join(timeout=5)

    console.print(Rule(style="blue"))

    if not result_box:
        console.print(Panel("Agent did not return a result.", title="❌ Failed", border_style="red"))
        return

    result, success = result_box[0]

    if success:
        console.print(
            Panel(
                str(result),
                title="✅ Result",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                str(result),
                title="❌ Failed",
                border_style="red",
                padding=(1, 2),
            )
        )


# ── Main Loop ────────────────────────────────────────────────────────

def main():
    print_banner()
    print_help()

    while True:
        try:
            user_input = console.input("[bold green]>>> [/bold green]").strip()

            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd == "exit":
                console.print("[bold red]Goodbye![/bold red]")
                sys.exit(0)

            elif cmd == "help":
                print_help()

            else:
                image_path = console.input("[bold green]Attach an image path (press Enter to skip): [/bold green]").strip()
                
                loaded_image = None
                if image_path:
                    # Strip extra shell quotes from drop
                    image_path = image_path.strip('\'"')
                    try:
                        from PIL import Image
                        loaded_image = Image.open(image_path)
                    except Exception as e:
                        console.print(f"[bold red]Failed to load image: {e}[/bold red]")
                        continue
                        
                handle_task(user_input, loaded_image)

        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
            sys.exit(0)

        except Exception as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            # Never crash — return to the >>> prompt


if __name__ == "__main__":
    main()
