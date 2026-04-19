import os
from smolagents import tool
from nylas import Client
from tools.human_confirm import ask_human_confirmation

# Initialize the Nylas client (Make sure these are in your .env file!)
nylas_client = Client(
    api_key=os.environ.get("NYLAS_API_KEY"),
    api_uri="https://api.us.nylas.com" # Or EU depending on your region
)

@tool
def schedule_meeting(title: str, start_time: int, end_time: int, participant_emails: list[str]) -> str:
    """Schedules a calendar meeting and sends invites.
    
    Args:
        title: The name of the meeting.
        start_time: Unix timestamp of when the meeting starts.
        end_time: Unix timestamp of when the meeting ends.
        participant_emails: A list of email addresses to invite.
    """
    # 1. ALWAYS ask for confirmation before sending real invites!
    confirmation = ask_human_confirmation(f"Schedule '{title}' with {participant_emails}?")
    if "denied" in confirmation.lower():
        return "Task cancelled by user."

    # 2. Format the participants for Nylas
    participants = [{"email": email} for email in participant_emails]
    grant_id = os.environ.get("NYLAS_GRANT_ID") # Your connected calendar ID

    # 3. Create the event using the Nylas SDK
    try:
        event = nylas_client.events.create(
            identifier=grant_id,
            request_body={
                "title": title,
                "when": {
                    "start_time": start_time,
                    "end_time": end_time,
                },
                "participants": participants,
                "conferencing": {
                    "provider": "Google Meet",
                    "autocreate": True
                }
            }
        )
        return f"Success! Meeting scheduled. Link: {event.data.conferencing.details.url}"
    except Exception as e:
        return f"Failed to schedule meeting: {str(e)}"