# Calendar Skill

> **Owner:** Default

## Description

This skill enables you to schedule Google Meet calendar events and send invitations to participants autonomously using the Nylas integration.

## Trigger Conditions

Use this skill whenever the user asks you to:
- "Create a meeting"
- "Schedule an appointment"
- "Make a calendar event"
- "Create a google meet link"

## Instructions

1. Identify the meeting title, start time, end time, and the list of participant email addresses from the user's prompt. 
2. If the user doesn't specify an exact time, use your reasoning to figure out a logical timestamp (e.g. converting "tomorrow at 3 PM" to the UNIX epoch format utilizing the standard Python `time` and `datetime` libraries inside your sandbox). Default to 30-minute meetings if duration is missing.
3. Use the `schedule_meeting` tool to create the calendar event.
4. Provide the generated link returned by the tool to the user!

## Output Format

A friendly message confirming the meeting has been scheduled along with the meeting URL (if generated).
