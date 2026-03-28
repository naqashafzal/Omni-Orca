"""
calendar_agent.py
Google Calendar integration for reading events and booking meetings.
Uses OAuth2 with token caching — only asks to log in ONCE, then auto-refreshes.
"""

import os
import json
import datetime

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Calendar read + write scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_credentials.json")


class CalendarAgent:
    def __init__(self):
        self.service = None
        self._authenticated = False
        if GOOGLE_AVAILABLE:
            self._try_auto_auth()

    def _try_auto_auth(self):
        """Try to authenticate using cached token without user interaction."""
        if not os.path.exists(CREDENTIALS_FILE):
            return  # Credentials file not set up yet

        try:
            creds = None
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    return  # Needs interactive auth

            self.service = build("calendar", "v3", credentials=creds)
            self._authenticated = True
        except Exception as e:
            print(f"[Calendar] Auto-auth failed: {e}")

    def authenticate(self) -> str:
        """
        Runs the Google OAuth2 login flow in the browser (one-time setup).
        Requires calendar_credentials.json from Google Cloud Console.
        """
        if not GOOGLE_AVAILABLE:
            return "Error: google-api-python-client not installed."

        if not os.path.exists(CREDENTIALS_FILE):
            return (
                "❌ calendar_credentials.json not found!\n\n"
                "SETUP STEPS:\n"
                "1. Go to https://console.cloud.google.com\n"
                "2. Create a project\n"
                "3. Enable 'Google Calendar API'\n"
                "4. Create OAuth2 credentials (Desktop App)\n"
                "5. Download the JSON and save it as 'calendar_credentials.json' in the neural-automater folder\n"
                "6. Then try again!"
            )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

            self.service = build("calendar", "v3", credentials=creds)
            self._authenticated = True
            return "✅ Google Calendar connected successfully!"
        except Exception as e:
            return f"❌ Authentication failed: {e}"

    def get_upcoming_events(self, n: int = 5) -> str:
        """Returns the next N calendar events."""
        if not self._authenticated:
            return "Not authenticated. Run authenticate() first."

        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=n,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])
            if not events:
                return "📅 No upcoming events found."

            output = f"📅 Your next {len(events)} events:\n\n"
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                output += f"• {event.get('summary', 'Untitled')}\n"
                output += f"  When: {start}\n"
                output += f"  Location: {event.get('location', 'Not specified')}\n\n"

            return output.strip()
        except Exception as e:
            return f"Error fetching events: {e}"

    def get_todays_briefing(self) -> str:
        """Returns a plain-English summary of today's schedule for the AI."""
        if not self._authenticated:
            return "Calendar not connected. No schedule available."

        today = datetime.date.today()
        start = datetime.datetime.combine(today, datetime.time.min).isoformat() + "Z"
        end = datetime.datetime.combine(today, datetime.time.max).isoformat() + "Z"

        try:
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])
            if not events:
                return f"Today ({today.strftime('%A, %B %d')}) you have no scheduled events. Your day is clear!"

            output = f"Today ({today.strftime('%A, %B %d')}) you have {len(events)} event(s):\n"
            for event in events:
                time_str = event["start"].get("dateTime", "All day")
                if "T" in time_str:
                    dt = datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    time_str = dt.strftime("%I:%M %p")
                output += f"  • {time_str}: {event.get('summary', 'Untitled')}\n"

            return output
        except Exception as e:
            return f"Error reading today's schedule: {e}"

    def create_event(self, title: str, date: str, start_time: str, end_time: str = None, description: str = "") -> str:
        """
        Creates a new Google Calendar event.
        date format: YYYY-MM-DD
        time format: HH:MM (24-hour)
        """
        if not self._authenticated:
            return "Not authenticated."

        try:
            if not end_time:
                # Default to 1-hour event
                start_dt = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + datetime.timedelta(hours=1)
                end_time = end_dt.strftime("%H:%M")

            start_full = f"{date}T{start_time}:00"
            end_full = f"{date}T{end_time}:00"

            event = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_full, "timeZone": "Asia/Karachi"},
                "end": {"dateTime": end_full, "timeZone": "Asia/Karachi"},
            }

            result = self.service.events().insert(calendarId="primary", body=event).execute()
            return f"✅ Event created: '{title}' on {date} at {start_time}\nLink: {result.get('htmlLink')}"
        except Exception as e:
            return f"❌ Failed to create event: {e}"


if __name__ == "__main__":
    agent = CalendarAgent()
    if not agent._authenticated:
        print("Run authenticate() to connect your Google Calendar.")
    else:
        print(agent.get_upcoming_events(3))
