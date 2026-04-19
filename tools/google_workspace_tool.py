"""
google_workspace_tool.py
------------------------
Google Workspace integration tools for the Synergy Agent.

Provides real Google API access for:
  - Google Calendar (create events with Meet links)
  - Gmail API (send emails)
  - Google Sheets (create, read, write)
  - Google Docs (create documents)
  - Google Drive (upload files, share)

Authentication:
  - Uses OAuth 2.0 with browser-based consent on first run.
  - Requires a `credentials.json` file from Google Cloud Console
    at the project root.
  - Saves `token.json` after first login for future sessions.

Dependencies:
  pip install google-auth google-auth-oauthlib google-api-python-client
"""

import os
import json
import logging
import base64
import mimetypes
from datetime import datetime, timedelta

from smolagents import tool
from tools.human_confirm import ask_human_confirmation

logger = logging.getLogger("google_workspace")

# ── Paths ─────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
_CREDENTIALS_FILE = os.path.join(_PROJECT_ROOT, "credentials.json")
_TOKEN_FILE = os.path.join(_PROJECT_ROOT, "token.json")

# ── Scopes — requested on first OAuth login ───────────────────────────
_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


# ══════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════

def _get_credentials():
    """
    Load or create Google OAuth2 credentials.
    On first run, opens a browser for consent.
    Returns a google.oauth2.credentials.Credentials object.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None

    # Load existing token
    if os.path.exists(_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(_TOKEN_FILE, _SCOPES)

    # Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google credentials.json not found at {_CREDENTIALS_FILE}. "
                    "Download it from https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                _CREDENTIALS_FILE, _SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save for next time
        with open(_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def _build_service(api: str, version: str):
    """Build a Google API service client."""
    from googleapiclient.discovery import build
    creds = _get_credentials()
    return build(api, version, credentials=creds)


# ══════════════════════════════════════════════════════════════════════
# Tool 1: Authentication
# ══════════════════════════════════════════════════════════════════════

@tool
def google_auth_login() -> str:
    """Authenticate with Google via OAuth2. On first use, opens a browser
    window for Google login and consent. Saves credentials to token.json
    for all future sessions. Call this before using any other Google tool.

    Returns:
        str: Confirmation message confirming authentication is ready.
    """
    try:
        creds = _get_credentials()
        # Verify credentials are valid by checking token presence
        if creds and creds.valid:
            return f"✅ Google authentication successful. Token saved to {_TOKEN_FILE}. You can now use Google Workspace tools."
        elif creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(_TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            return f"✅ Google token refreshed successfully. You can now use Google Workspace tools."
        else:
            return "❌ Google credentials could not be validated. Please re-authenticate."
    except FileNotFoundError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Google authentication failed: {str(e)}"


# ══════════════════════════════════════════════════════════════════════
# Tool 2: Google Calendar + Meet
# ══════════════════════════════════════════════════════════════════════

@tool
def google_create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: str = "",
    add_meet_link: str = "true",
    timezone: str = "Asia/Kolkata",
) -> str:
    """Create a Google Calendar event with an optional Google Meet link.

    Args:
        title: Title/summary of the calendar event.
        start_time: Start time in ISO format (e.g. '2026-04-20T10:00:00').
        end_time: End time in ISO format (e.g. '2026-04-20T11:00:00').
        description: Optional description or agenda for the event.
        attendees: Comma-separated email addresses of attendees
                   (e.g. 'a@x.com,b@x.com'). Leave empty for no attendees.
        add_meet_link: Set to 'true' to generate a Google Meet link,
                       'false' to skip. Defaults to 'true'.
        timezone: Timezone string (default: 'Asia/Kolkata').

    Returns:
        str: JSON with event ID, HTML link, and Meet link (if created).
    """
    attendee_list = [
        e.strip() for e in attendees.split(",") if e.strip()
    ] if attendees.strip() else []

    # Human confirmation for events with attendees
    if attendee_list:
        confirmation = ask_human_confirmation(
            action=f"Create calendar event '{title}' and invite {len(attendee_list)} attendee(s)",
            reason=f"Event: {title} | {start_time} to {end_time}",
            risk_level="MEDIUM",
            details=json.dumps({
                "Title": title,
                "Start": start_time,
                "End": end_time,
                "Attendees": ", ".join(attendee_list),
                "Meet Link": add_meet_link,
            }),
        )
        if confirmation.strip().upper() != "YES":
            return json.dumps({"status": "cancelled", "message": f"User declined: {confirmation}"})

    try:
        service = _build_service("calendar", "v3")

        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
        }

        if attendee_list:
            event_body["attendees"] = [{"email": e} for e in attendee_list]

        if add_meet_link.lower() == "true":
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"synergy-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1 if add_meet_link.lower() == "true" else 0,
            sendUpdates="all" if attendee_list else "none",
        ).execute()

        result = {
            "status": "created",
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
        }

        # Extract Meet link if present
        conference = event.get("conferenceData", {})
        entry_points = conference.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                result["meet_link"] = ep.get("uri")
                break

        if attendee_list:
            result["attendees_invited"] = attendee_list

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Tool 3: Gmail API
# ══════════════════════════════════════════════════════════════════════

@tool
def google_send_email(to: str, subject: str, body: str, is_html: str = "false") -> str:
    """Send an email using the Gmail API (OAuth2 authenticated).
    Supports plain text and HTML bodies. Always asks for human
    confirmation before sending.

    Args:
        to: Recipient email address (e.g. 'user@example.com').
        subject: Subject line of the email.
        body: Body content of the email (plain text or HTML).
        is_html: Set to 'true' if body is HTML, 'false' for plain text.
                 Defaults to 'false'.

    Returns:
        str: Confirmation message with message ID, or error.
    """
    confirmation = ask_human_confirmation(
        action=f"Send email to {to}",
        reason=f"Subject: {subject}",
        risk_level="MEDIUM",
        details=json.dumps({"To": to, "Subject": subject}),
    )
    if confirmation.strip().upper() != "YES":
        return f"❌ Email cancelled by user. (Response: '{confirmation}')"

    try:
        import email.mime.text as mime_text
        import email.mime.multipart as mime_multi

        service = _build_service("gmail", "v1")

        message = mime_multi.MIMEMultipart()
        message["to"] = to
        message["subject"] = subject

        content_type = "html" if is_html.lower() == "true" else "plain"
        message.attach(mime_text.MIMEText(body, content_type))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_result = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

        return f"✅ Email sent to {to}. Message ID: {send_result.get('id')}"

    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"


# ══════════════════════════════════════════════════════════════════════
# Tool 4: Google Sheets — Create
# ══════════════════════════════════════════════════════════════════════

@tool
def google_create_spreadsheet(title: str, sheet_data: str = "") -> str:
    """Create a new Google Spreadsheet. Optionally populate it with
    initial data.

    Args:
        title: Title of the new spreadsheet.
        sheet_data: Optional JSON string representing rows to write.
                    Format: '[["Header1","Header2"],["val1","val2"]]'
                    Leave empty to create a blank spreadsheet.

    Returns:
        str: JSON with spreadsheet ID and URL.
    """
    try:
        service = _build_service("sheets", "v4")

        spreadsheet = service.spreadsheets().create(
            body={"properties": {"title": title}},
            fields="spreadsheetId,spreadsheetUrl",
        ).execute()

        spreadsheet_id = spreadsheet.get("spreadsheetId")
        spreadsheet_url = spreadsheet.get("spreadsheetUrl")

        # Optionally write initial data
        if sheet_data and sheet_data.strip():
            try:
                rows = json.loads(sheet_data)
                if rows:
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range="Sheet1!A1",
                        valueInputOption="USER_ENTERED",
                        body={"values": rows},
                    ).execute()
            except json.JSONDecodeError:
                logger.warning("sheet_data is not valid JSON, skipping initial data write")

        return json.dumps({
            "status": "created",
            "spreadsheet_id": spreadsheet_id,
            "url": spreadsheet_url,
        }, indent=2)

    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Tool 5: Google Sheets — Read
# ══════════════════════════════════════════════════════════════════════

@tool
def google_read_spreadsheet(spreadsheet_id: str, range_notation: str = "Sheet1!A1:Z1000") -> str:
    """Read data from a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet (from the URL).
        range_notation: The A1 range to read (default: 'Sheet1!A1:Z1000').

    Returns:
        str: JSON array of rows, where each row is an array of cell values.
    """
    try:
        service = _build_service("sheets", "v4")
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_notation)
            .execute()
        )
        values = result.get("values", [])
        return json.dumps({"status": "success", "rows": values, "row_count": len(values)}, indent=2)
    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Tool 6: Google Sheets — Write / Append
# ══════════════════════════════════════════════════════════════════════

@tool
def google_write_spreadsheet(spreadsheet_id: str, data: str, range_notation: str = "Sheet1!A1", mode: str = "append") -> str:
    """Write or append data to a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        data: JSON string of rows to write. Format: '[["a","b"],["c","d"]]'.
        range_notation: A1 range for where to write (default: 'Sheet1!A1').
                        For append mode, this determines the table to append to.
        mode: 'append' to add rows at the bottom, 'overwrite' to replace
              existing data at the specified range. Defaults to 'append'.

    Returns:
        str: JSON confirmation with updated cell count.
    """
    try:
        rows = json.loads(data)
    except json.JSONDecodeError:
        return json.dumps({"status": "failed", "message": "data is not valid JSON"})

    try:
        service = _build_service("sheets", "v4")

        if mode == "append":
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": rows},
                )
                .execute()
            )
            updates = result.get("updates", {})
            return json.dumps({
                "status": "appended",
                "updated_range": updates.get("updatedRange"),
                "updated_rows": updates.get("updatedRows"),
            }, indent=2)
        else:
            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption="USER_ENTERED",
                    body={"values": rows},
                )
                .execute()
            )
            return json.dumps({
                "status": "overwritten",
                "updated_range": result.get("updatedRange"),
                "updated_cells": result.get("updatedCells"),
            }, indent=2)

    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Tool 7: Google Docs
# ══════════════════════════════════════════════════════════════════════

@tool
def google_create_document(title: str, content: str = "") -> str:
    """Create a new Google Document with optional structured content.

    Args:
        title: Title of the new document.
        content: Plain text content to insert into the document.
                 Supports newlines for paragraphs. Leave empty for blank doc.

    Returns:
        str: JSON with document ID and URL.
    """
    try:
        docs_service = _build_service("docs", "v1")
        drive_service = _build_service("drive", "v3")

        # Create blank doc
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")

        # Insert content if provided
        if content and content.strip():
            requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": content,
                    }
                }
            ]
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        return json.dumps({
            "status": "created",
            "document_id": doc_id,
            "url": doc_url,
        }, indent=2)

    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Tool 8: Google Drive
# ══════════════════════════════════════════════════════════════════════

@tool
def google_upload_to_drive(
    file_path: str,
    folder_id: str = "",
    share_with: str = "",
    share_role: str = "reader",
) -> str:
    """Upload a file to Google Drive and optionally share it.

    Args:
        file_path: Absolute path to the local file to upload.
        folder_id: Optional Drive folder ID to upload into.
                   Leave empty to upload to root (My Drive).
        share_with: Optional comma-separated email addresses to share
                    the file with (e.g. 'a@x.com,b@x.com').
        share_role: Permission role: 'reader', 'writer', or 'commenter'.
                    Defaults to 'reader'.

    Returns:
        str: JSON with file ID, web link, and sharing results.
    """
    if not os.path.exists(file_path):
        return json.dumps({"status": "failed", "message": f"File not found: {file_path}"})

    share_list = [
        e.strip() for e in share_with.split(",") if e.strip()
    ] if share_with.strip() else []

    # Confirm if sharing with people
    if share_list:
        confirmation = ask_human_confirmation(
            action=f"Upload '{os.path.basename(file_path)}' to Drive and share with {len(share_list)} people",
            reason="File will be accessible to the specified users.",
            risk_level="MEDIUM",
            details=json.dumps({
                "File": os.path.basename(file_path),
                "Share with": ", ".join(share_list),
                "Permission": share_role,
            }),
        )
        if confirmation.strip().upper() != "YES":
            return json.dumps({"status": "cancelled", "message": f"User declined: {confirmation}"})

    try:
        from googleapiclient.http import MediaFileUpload

        service = _build_service("drive", "v3")

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_metadata = {"name": os.path.basename(file_path)}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id,webViewLink")
            .execute()
        )

        result = {
            "status": "uploaded",
            "file_id": uploaded.get("id"),
            "web_link": uploaded.get("webViewLink"),
        }

        # Share with specified users
        if share_list:
            shared_with = []
            for email in share_list:
                try:
                    service.permissions().create(
                        fileId=uploaded["id"],
                        body={
                            "type": "user",
                            "role": share_role,
                            "emailAddress": email,
                        },
                        sendNotificationEmail=True,
                    ).execute()
                    shared_with.append(email)
                except Exception as share_err:
                    logger.warning(f"Failed to share with {email}: {share_err}")
            result["shared_with"] = shared_with

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})


# ══════════════════════════════════════════════════════════════════════
# Export list for __init__.py
# ══════════════════════════════════════════════════════════════════════

GOOGLE_WORKSPACE_TOOLS = [
    google_auth_login,
    google_create_calendar_event,
    google_send_email,
    google_create_spreadsheet,
    google_read_spreadsheet,
    google_write_spreadsheet,
    google_create_document,
    google_upload_to_drive,
]


# ══════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Google Workspace Tool — Self Test")
    print("=" * 50)
    print(f"  credentials.json exists: {os.path.exists(_CREDENTIALS_FILE)}")
    print(f"  token.json exists:       {os.path.exists(_TOKEN_FILE)}")
    print(f"  Tools registered:        {len(GOOGLE_WORKSPACE_TOOLS)}")
    for t in GOOGLE_WORKSPACE_TOOLS:
        print(f"    - {t.name}")
    print("\nTo authenticate, run: google_auth_login()")
