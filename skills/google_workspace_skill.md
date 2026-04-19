# Google Workspace Skill

## ⚠️ MANDATORY — USE ONLY THE PROVIDED TOOLS
**You MUST use the provided Google tool functions listed below. Do NOT write your own code to call Google APIs directly. Do NOT import google.oauth2, googleapiclient, or any Google library yourself. The tools handle authentication and API calls internally. Just call the tool functions.**

Available Google tools:
- `google_auth_login()` — authenticate with Google
- `google_create_calendar_event(title, start_time, end_time, description, attendees, add_meet_link, timezone)` — create calendar event + Meet link
- `google_send_email(to, subject, body, is_html)` — send email via Gmail API
- `google_create_spreadsheet(title, sheet_data)` — create Google Sheet
- `google_read_spreadsheet(spreadsheet_id, range_notation)` — read from Sheet
- `google_write_spreadsheet(spreadsheet_id, data, range_notation, mode)` — write/append to Sheet
- `google_create_document(title, content)` — create Google Doc
- `google_upload_to_drive(file_path, folder_id, share_with, share_role)` — upload to Drive

When the user asks you to perform any task involving Google services (Calendar, Meet, Gmail API, Sheets, Docs, Drive), follow this workflow:

## STEP 1: Authenticate (Optional)
- Call `google_auth_login()` first to check authentication status.
- **IMPORTANT: If `google_auth_login()` fails, do NOT give up.** Skip authentication and proceed directly to Step 2. The operation tools (like `google_create_spreadsheet`) handle authentication internally and will work even if `google_auth_login()` reports an error.
- Only stop if the operation tool itself returns a credential error.

## STEP 2: Parse Input Data
- If the task involves a CSV or list of people (e.g. attendees, recipients), use `read_file` to read the data first.
- Validate email addresses before using them.
- If data is malformed or missing, STOP and ask the user.

## STEP 3: Execute the Workflow

### For Calendar / Meeting Tasks:
Example:
```python
result = google_create_calendar_event(
    title="Team Standup",
    start_time="2026-04-20T10:00:00",
    end_time="2026-04-20T10:30:00",
    description="Daily standup meeting",
    attendees="alice@example.com,bob@example.com",
    add_meet_link="true",
    timezone="Asia/Kolkata"
)
print(result)
```

### For Spreadsheet Tasks:
Example — create a sheet with headers and data:
```python
result = google_create_spreadsheet(
    title="Hackathon Tasks",
    sheet_data='[["Task","Assignee","Status"],["Build UI","Alice","In Progress"],["Write API","Bob","Done"]]'
)
print(result)
```

### For Email Tasks (via Gmail API):
Example:
```python
result = google_send_email(
    to="user@example.com",
    subject="Meeting Invite",
    body="Hi, please join our meeting tomorrow at 10 AM.",
    is_html="false"
)
print(result)
```

### For Document Tasks:
Example:
```python
result = google_create_document(
    title="Meeting Notes",
    content="Meeting Notes\n\nDate: April 20, 2026\nAttendees: Alice, Bob\n\nAgenda:\n1. Review sprint\n2. Plan next steps"
)
print(result)
```

### For Drive Tasks:
Example:
```python
result = google_upload_to_drive(
    file_path="/path/to/report.pdf",
    share_with="alice@example.com,bob@example.com",
    share_role="reader"
)
print(result)
```

## STEP 4: Human Confirmation
- The Google tools **automatically** call `ask_human_confirmation()` before:
  - Creating events with attendees
  - Sending emails
  - Sharing files on Drive
- You do NOT need to call `ask_human_confirmation()` separately for these actions.
- For other destructive actions not covered above, call `ask_human_confirmation()` yourself.

## STEP 5: Report Results
- Return all generated links (Meet link, Sheet URL, Doc URL, Drive link).
- Report the number of attendees invited or emails sent.
- List any failures or skipped items.

## CRITICAL RULES
- **NEVER import google.oauth2, googleapiclient, or any Google library. ONLY use the tool functions listed above.**
- **If google_auth_login() fails, STILL try the actual operation tool. Do NOT give up.**
- NEVER simulate or fake Google API calls.
- NEVER hardcode API keys or secrets.
- All times must be in ISO 8601 format (e.g. `2026-04-20T10:00:00`).
- Default timezone is `Asia/Kolkata` unless the user specifies otherwise.
