# OWNER: Person 2
"""
email_tool.py
-------------
Allows the agent to send emails via Gmail SMTP.

First-time flow:
  1. Opens the Google App Password page in the user's browser so they can
     generate an App Password (required because Google blocks plain passwords
     for third-party apps).
  2. Prompts the user in the terminal for their Gmail address and the
     App Password they just created.
  3. Saves both values to tools/email_creds.txt for all future sessions.

Subsequent runs:
  - Credentials are loaded from tools/email_creds.txt automatically.
  - The user is never asked to log in again.

IMPORTANT: Always calls ask_human_confirmation before actually sending,
because sending an email is irreversible.
"""

import os
import smtplib
import webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from smolagents import tool

from tools.human_confirm import ask_human_confirmation

console = Console()

# Path where credentials are stored (inside the tools folder)
CREDS_FILE = os.path.join(os.path.dirname(__file__), "email_creds.txt")

# Gmail SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_credentials() -> tuple[str, str] | None:
    """
    Load saved Gmail credentials from file.

    Returns:
        (email, app_password) tuple, or None if the file doesn't exist.
    """
    if not os.path.exists(CREDS_FILE):
        return None

    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()

    if len(lines) < 2:
        return None  # File is malformed — treat as missing

    email    = lines[0].split("=", 1)[1].strip()
    password = lines[1].split("=", 1)[1].strip()
    return email, password


def _save_credentials(email: str, password: str) -> None:
    """
    Persist Gmail credentials to tools/email_creds.txt.
    Format is plain text (key=value) as requested.
    """
    with open(CREDS_FILE, "w", encoding="utf-8") as f:
        f.write(f"EMAIL={email}\n")
        f.write(f"APP_PASSWORD={password}\n")

    console.print(f"\n[green]✓ Credentials saved to:[/green] {CREDS_FILE}")


def _setup_credentials() -> tuple[str, str]:
    """
    First-time setup:
      - Opens Google's App Password page in the browser.
      - Prompts the user to enter their Gmail + App Password.
      - Saves and returns the credentials.
    """
    console.print(Panel(
        "[bold white]First-time email setup[/bold white]\n\n"
        "Gmail requires an [bold cyan]App Password[/bold cyan] for third-party apps.\n"
        "The browser will open Google's App Password page.\n\n"
        "[dim]Steps:[/dim]\n"
        "  1. Sign in to your Google account if prompted\n"
        "  2. Under 'Select app' choose [bold]Mail[/bold]\n"
        "  3. Under 'Select device' choose [bold]Other[/bold] → type [bold]Synergy Agent[/bold]\n"
        "  4. Click [bold]Generate[/bold] and copy the 16-character password\n"
        "  5. Come back here and paste it below",
        title="[bold yellow]📧 Gmail Setup[/bold yellow]",
        border_style="yellow",
    ))

    console.print()
    email    = Prompt.ask("[bold]Your Gmail address[/bold]")

    console.print("\n[dim]Opening browser...[/dim]")
    webbrowser.open("https://myaccount.google.com/apppasswords")

    console.print()
    password = Prompt.ask("[bold]App Password (16 chars, spaces ok)[/bold]", password=True)

    # Strip spaces from app password (Google displays it as "xxxx xxxx xxxx xxxx")
    password = password.replace(" ", "")

    _save_credentials(email, password)
    return email, password


def _get_credentials() -> tuple[str, str]:
    """
    Return credentials from file, or trigger first-time setup if missing.
    """
    creds = _load_credentials()
    if creds:
        return creds
    return _setup_credentials()


# ---------------------------------------------------------------------------
# Public smolagents @tool
# ---------------------------------------------------------------------------

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email from the user's saved Gmail account. On first use, opens
    the browser so the user can generate a Gmail App Password, then stores the
    credentials locally for all future sessions. Always asks for human
    confirmation before sending because email is irreversible.

    Args:
        to: Recipient email address (e.g. 'alice@example.com').
        subject: Subject line of the email.
        body: Plain-text body of the email.

    Returns:
        str: 'sent' on success, or an error/cancellation message.
    """
    # Step 1 — load or collect credentials
    try:
        sender_email, app_password = _get_credentials()
    except Exception as e:
        return f"Failed to set up email credentials: {e}"

    # Step 2 — ask human before sending (irreversible action)
    import json
    response = ask_human_confirmation(
        action=f"Send email to: {to}",
        reason=f"Subject: {subject}",
        risk_level="MEDIUM",
        details=json.dumps({"From": sender_email, "To": to, "Subject": subject}),
    )

    if response.strip().upper() != "YES":
        return f"Email cancelled by user. (Response: '{response}')"

    # Step 3 — build and send the message
    try:
        msg = MIMEMultipart()
        msg["From"]    = sender_email
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to, msg.as_string())

        return f"Email sent successfully to {to}."

    except smtplib.SMTPAuthenticationError:
        return (
            "Authentication failed. Your App Password may be wrong or expired.\n"
            f"Delete '{CREDS_FILE}' and try again to reset credentials."
        )
    except Exception as e:
        return f"Failed to send email: {e}"


@tool
def reset_email_credentials() -> str:
    """Delete the saved Gmail credentials file so the user can log in again
    with a different account or a new App Password. Safe to call any time.

    Returns:
        str: Confirmation message.
    """
    if os.path.exists(CREDS_FILE):
        os.remove(CREDS_FILE)
        return f"Credentials cleared. Next email send will trigger setup again."
    return "No credentials file found — nothing to reset."


# ---------------------------------------------------------------------------
# TEST BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    console.print("\n[bold]Testing email_tool.py[/bold]\n")

    console.print("[dim]--- Test 1: Credential loading ---[/dim]")
    creds = _load_credentials()
    if creds:
        console.print(f"[green]✓ Credentials found:[/green] {creds[0]}")
    else:
        console.print("[yellow]No saved credentials. Run send_email() to trigger setup.[/yellow]")

    console.print("\n[dim]--- Test 2: send_email (dry run, will ask confirmation) ---[/dim]")
    result = send_email(
        to="test@example.com",
        subject="Synergy Agent Test",
        body="This is a test email from the Synergy Agent email tool.",
    )
    console.print(f"Result: [bold cyan]{result}[/bold cyan]")
