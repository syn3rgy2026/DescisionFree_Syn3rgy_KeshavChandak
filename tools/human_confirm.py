# OWNER: Person 2
"""
human_confirm.py
----------------
Interrupts the agentic loop to request explicit human approval before
the agent takes a sensitive or irreversible action (e.g. running a
destructive shell command, sending an email, deleting files).

Uses rich for a clearly-formatted confirmation prompt.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

# --- THE OFFICIAL FUNCTION FROM THE PROJECT GUIDE ---

def ask_human_confirmation(action: str, reason: str, risk_level: str) -> str:
    """
    The official function required by SYNERGY_AGENT_GUIDE.md.
    
    Args:
        action (str): What the agent wants to do.
        reason (str): Why it wants to do it.
        risk_level (str): LOW, MEDIUM, or HIGH.
        
    Returns:
        str: "YES", "NO", or custom alternative instructions.
    """
    # Determine the color based on the risk level
    risk_color = "green"
    if risk_level.upper() == "MEDIUM":
        risk_color = "yellow"
    elif risk_level.upper() == "HIGH":
        risk_color = "red"

    # Build the text content for the UI panel
    content = (
        f"[bold white]Action:[/bold white] {action}\n"
        f"[bold white]Reason:[/bold white] {reason}\n"
        f"[bold white]Risk:[/bold white] [{risk_color}]{risk_level.upper()}[/{risk_color}]"
    )
    
    # Create a beautiful Rich Panel
    panel = Panel(
        content,
        title="[bold red]🛑 HUMAN CONFIRMATION REQUIRED 🛑[/bold red]",
        border_style=risk_color
    )
    
    console.print(panel)
    console.print("[dim]Type [bold green]YES[/bold green] to allow, [bold red]NO[/bold red] to cancel, or type [bold cyan]alternative instructions[/bold cyan].[/dim]")
    
    # Use Prompt.ask so we return a STRING, not just a boolean
    response = Prompt.ask("❯")
    return response


# --- THE ORIGINAL BOILERPLATE IMPLEMENTATION ---

def ask(action_description: str) -> bool:
    """
    Display a confirmation prompt and return the user's yes/no decision.

    Args:
        action_description (str): Human-readable description of the action
                                  the agent wants to take.

    Returns:
        bool: True if the user approved, False otherwise.
    """
    console.print(f"\n[bold yellow]⚠️  AGENT ACTION REQUIRED[/bold yellow]")
    return Confirm.ask(f"[bold white]{action_description}[/bold white]")


def ask_with_detail(action_description: str, details: dict) -> bool:
    """
    Show a detailed breakdown of an action before asking for confirmation.

    Args:
        action_description (str): Short description of the action.
        details (dict): Key-value pairs with extra context (e.g. command, path).

    Returns:
        bool: True if approved.
    """
    # Format the dictionary details nicely
    details_str = "\n".join([f"[cyan]{k}:[/cyan] {v}" for k, v in details.items()])
    
    panel = Panel(
        f"[bold white]{action_description}[/bold white]\n\n{details_str}",
        title="[bold yellow]Agent Action Confirmation[/bold yellow]",
        border_style="yellow"
    )
    console.print(panel)
    return Confirm.ask("Do you approve this action?")


# --- TEST BLOCK FOR PERSON 2 ---
if __name__ == "__main__":
    print("\n" + "="*40)
    print("TESTING HUMAN CONFIRM TOOL (PERSON 2)")
    print("="*40 + "\n")

    # 1. Testing the Guide's required function
    console.print("[bold magenta]--- Testing ask_human_confirmation (Guide Requirement) ---[/bold magenta]")
    user_input = ask_human_confirmation(
        action="Run shell command: `rm -rf /`",
        reason="The user asked to clean up the system, so I am wiping the hard drive.",
        risk_level="HIGH"
    )
    console.print(f"\n[System] You entered: '[bold cyan]{user_input}[/bold cyan]'\n")
    
    # 2. Testing boilerplate ask()
    console.print("[bold magenta]--- Testing boilerplate ask() ---[/bold magenta]")
    res1 = ask("Delete temporary cache files?")
    console.print(f"[System] You chose: [bold cyan]{res1}[/bold cyan]\n")
    
    # 3. Testing boilerplate ask_with_detail()
    console.print("[bold magenta]--- Testing boilerplate ask_with_detail() ---[/bold magenta]")
    res2 = ask_with_detail("Execute Python Script", {"Script": "scraper.py", "Timeout": "30s"})
    console.print(f"[System] You chose: [bold cyan]{res2}[/bold cyan]\n")
    
    print("Testing complete!")