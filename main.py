"""
main.py
-------
CLI entry point for Synergy Agent.
Provides the interactive >>> loop, dispatches tasks to the agent,
and handles errors so the CLI never crashes.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from agent.core_agent import run_agent
from agent.error_recovery import run_with_recovery

console = Console()


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

def handle_task(task: str):
    """
    Run the agent with recovery and display the result.
    Agent step output (Thought / Tool / Observation) prints freely.
    """
    console.print(Rule("[bold blue]Agent Starting[/bold blue]", style="blue"))
    result, success = run_with_recovery(run_agent, task)
    console.print(Rule(style="blue"))

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
                handle_task(user_input)

        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
            sys.exit(0)

        except Exception as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            # Never crash — return to the >>> prompt


if __name__ == "__main__":
    main()
