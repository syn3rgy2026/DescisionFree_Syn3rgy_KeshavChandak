# OWNER: Person 2
"""
email_reader_tool.py
--------------------
Allows the agent to fetch and summarise emails from the user's Gmail
inbox using IMAP over SSL (imap.gmail.com:993).

Credential sharing:
  - Reuses the same tools/email_creds.txt file as email_tool.py.
  - If the file is missing, the same browser-based setup flow is triggered
    (open Google App Password page → user enters Gmail + App Password → saved).
  - The user is never asked to log in again once credentials are stored.

Public tool:
  read_emails(count, folder, unread_only, filter_sender, filter_subject)

Returns a formatted string of email summaries the LLM agent can reason
about and present to the user.
"""

import imaplib
import email as email_lib
import os
import textwrap
from email.header import decode_header
from email.utils import parsedate_to_datetime

from rich.console import Console
from smolagents import tool

# Re-use the exact same credential helpers from email_tool — no duplication
from tools.email_tool import _get_credentials, CREDS_FILE

console = Console()

# Gmail IMAP settings
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

# Max characters of email body shown per email (keeps LLM context manageable)
BODY_PREVIEW_CHARS = 500


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _decode_header_value(raw_value: str) -> str:
    """Decode an encoded email header (e.g. UTF-8 base64 subjects) to a plain string."""
    if raw_value is None:
        return ""
    parts = decode_header(raw_value)
    decoded_parts = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(str(part))
    return " ".join(decoded_parts)


def _extract_body(msg) -> str:
    """
    Walk the email MIME structure and extract the plain-text body.
    Falls back to HTML body if no plain text is found.
    """
    plain_body = ""
    html_body  = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition  = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in disposition:
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue

            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")

            if content_type == "text/plain" and not plain_body:
                plain_body = text
            elif content_type == "text/html" and not html_body:
                html_body = text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            plain_body = payload.decode(charset, errors="replace")

    body = plain_body or html_body or "(no body)"
    # Strip excessive whitespace
    body = "\n".join(line.rstrip() for line in body.splitlines() if line.strip())
    return body


def _build_imap_search(unread_only: bool, filter_sender: str, filter_subject: str) -> str:
    """Build the IMAP SEARCH criteria string from the provided filters."""
    criteria_parts = []

    if unread_only:
        criteria_parts.append("UNSEEN")
    else:
        criteria_parts.append("ALL")

    if filter_sender.strip():
        criteria_parts.append(f'FROM "{filter_sender.strip()}"')

    if filter_subject.strip():
        criteria_parts.append(f'SUBJECT "{filter_subject.strip()}"')

    return " ".join(criteria_parts)


def _format_email(index: int, msg) -> str:
    """Format a single email into a readable block string."""
    subject = _decode_header_value(msg.get("Subject", "(no subject)"))
    sender  = _decode_header_value(msg.get("From",    "(unknown sender)"))
    date    = msg.get("Date", "(unknown date)")
    body    = _extract_body(msg)

    # Truncate body to keep output concise
    if len(body) > BODY_PREVIEW_CHARS:
        body = body[:BODY_PREVIEW_CHARS] + f"... [truncated — {len(body)} chars total]"

    # Wrap long lines for readability
    body = textwrap.fill(body, width=100)

    return (
        f"── Email {index} ──────────────────────────────────\n"
        f"From   : {sender}\n"
        f"Date   : {date}\n"
        f"Subject: {subject}\n"
        f"Body   :\n{body}\n"
    )


# ---------------------------------------------------------------------------
# Public smolagents @tool
# ---------------------------------------------------------------------------

@tool
def read_emails(
    count: int = 5,
    folder: str = "INBOX",
    unread_only: bool = False,
    filter_sender: str = "",
    filter_subject: str = "",
) -> str:
    """Fetch emails from the user's Gmail inbox and return their content as
    a formatted string so the agent can summarise or answer questions about them.
    On first use, opens the browser so the user can set up their Gmail App
    Password; credentials are then saved and reused automatically.

    Args:
        count: Number of most-recent emails to fetch (default 5, max 50).
        folder: Mailbox folder to read from — e.g. 'INBOX', '[Gmail]/Sent Mail',
                '[Gmail]/Spam'. Default is 'INBOX'.
        unread_only: If True, only fetch unread emails. Default False.
        filter_sender: Only return emails from this sender address (optional).
        filter_subject: Only return emails whose subject contains this text (optional).

    Returns:
        str: Formatted email summaries ready for the agent to read and summarise.
    """
    # Cap count to avoid flooding the LLM context
    count = min(max(1, count), 50)

    # Step 1 — get credentials (shared with email_tool.py)
    try:
        gmail_address, app_password = _get_credentials()
    except Exception as e:
        return f"Failed to load email credentials: {e}"

    # Step 2 — connect via IMAP SSL
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(gmail_address, app_password)
    except imaplib.IMAP4.error as e:
        return (
            f"IMAP login failed: {e}\n"
            f"Your App Password may be wrong or expired. "
            f"Delete '{CREDS_FILE}' and try again to reset credentials."
        )
    except Exception as e:
        return f"Failed to connect to Gmail IMAP: {e}"

    # Step 3 — select the folder
    status, _ = mail.select(f'"{folder}"')
    if status != "OK":
        mail.logout()
        return (
            f"Could not open folder '{folder}'. "
            "Common folders: INBOX, [Gmail]/Sent Mail, [Gmail]/Drafts, [Gmail]/Spam"
        )

    # Step 4 — search
    search_criteria = _build_imap_search(unread_only, filter_sender, filter_subject)
    status, message_ids = mail.search(None, search_criteria)
    if status != "OK":
        mail.logout()
        return f"Email search failed with criteria: {search_criteria}"

    ids = message_ids[0].split()
    if not ids:
        mail.logout()
        label = "unread " if unread_only else ""
        return f"No {label}emails found in '{folder}' matching your filters."

    # Take the last `count` emails (most recent last in IMAP)
    selected_ids = ids[-count:][::-1]  # reverse so newest is first

    # Step 5 — fetch and format
    results = []
    for idx, email_id in enumerate(selected_ids, start=1):
        status, data = mail.fetch(email_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            results.append(f"── Email {idx} ── [failed to fetch]\n")
            continue

        raw_email = data[0][1]
        msg = email_lib.message_from_bytes(raw_email)
        results.append(_format_email(idx, msg))

    mail.logout()

    header = (
        f"Fetched {len(results)} email(s) from '{folder}' "
        f"for {gmail_address}"
        + (" (unread only)" if unread_only else "")
        + (f" | from: {filter_sender}" if filter_sender else "")
        + (f" | subject contains: '{filter_subject}'" if filter_subject else "")
        + "\n\n"
    )
    return header + "\n".join(results)


# ---------------------------------------------------------------------------
# TEST BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    console.print("\n[bold]Testing email_reader_tool.py[/bold]\n")

    # Test 1 — fetch last 3 emails from inbox
    console.print("[dim]--- Test 1: Last 3 inbox emails ---[/dim]")
    output = read_emails(count=3)
    console.print(output)

    # Test 2 — unread only
    console.print("\n[dim]--- Test 2: Unread emails only ---[/dim]")
    output = read_emails(count=5, unread_only=True)
    console.print(output)
