import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.live import Live

console = Console()


def print_banner():
    banner = Panel(
        "[bold cyan]SYNERGY AGENT[/bold cyan]\n[dim]AI/ML Track — SYN3RGY 3.0[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    )
    console.print(banner)


def print_commands():
    table = Table(title="Available Commands", border_style="blue", header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("[bold]exit[/bold]",    "Quit the program")
    table.add_row("[bold]help[/bold]",    "Show this command list again")
    table.add_row("[bold]memory[/bold]",  "View memory (coming soon)")
    table.add_row("[bold]history[/bold]", "View task history (coming soon)")
    table.add_row("[bold]<task>[/bold]",  "Describe a task for the agent to execute")

    console.print(table)


def think():
    with Live(Spinner("dots", text="[yellow]Thinking...[/yellow]"), console=console, refresh_per_second=20):
        time.sleep(1)


def run_cli():
    print_banner()
    print_commands()
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold green]>>>[/bold green]").strip()
        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "exit":
            console.print("[bold red]Goodbye![/bold red]")
            break

        elif cmd == "help":
            print_commands()

        elif cmd == "memory":
            think()
            console.print("[yellow]Memory module not ready yet[/yellow]")

        elif cmd == "history":
            think()
            console.print("[yellow]History module not ready yet[/yellow]")

        else:
            think()
            console.print(
                f"[yellow]Agent module not ready yet. You typed:[/yellow] [bold white]{user_input}[/bold white]"
            )

        console.print()


if __name__ == "__main__":
    run_cli()
