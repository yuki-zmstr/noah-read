"""
Calendar Service for Noah - Handles Google Calendar integration for scheduling reading sessions
"""

import os
import datetime
import json
import tempfile
import base64
from typing import Dict, Optional
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for scheduling reading sessions in Google Calendar"""

    def __init__(self):
        self.enabled = False
        self.creds = None
        self.service = None
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.timezone = 'Asia/Tokyo'  # Set default timezone to UTC+9
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
        self.business_hours_start = 8  # 8 AM JST
        self.business_hours_end = 21   # 9 PM JST
        
        # Try to set up credentials
        if self.setup_credentials():
            self.enabled = True
            logger.info("Google Calendar service initialized successfully")
        else:
            self.enabled = False
            logger.error("Failed to initialize Google Calendar service")

    def setup_credentials(self):
        """Set up Google Calendar API credentials for local or deployment use."""

        def load_credentials_from_file():
            credentials_file = os.getenv(
                'GOOGLE_CALENDAR_CREDENTIALS_FILE', 'google_credentials.json')
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.abspath(
                os.path.join(base_dir, '..', credentials_file))
            return full_path if os.path.exists(full_path) else None

        def load_credentials_from_env():
            """Load credentials from an environment variable (used in deployment)."""
            creds_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not creds_str:
                raise RuntimeError(
                    "No credentials found: set GOOGLE_SERVICE_ACCOUNT_JSON env var")

            try:
                creds_str = base64.b64decode(creds_str).decode("utf-8")
            except Exception:
                pass  # Treat as raw JSON if not base64

            return json.loads(creds_str)

        try:
            credentials_path = load_credentials_from_file()

            if credentials_path:
                # 🧪 Local OAuth flow (Installed App)
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.scopes)
                self.creds = flow.run_local_server(port=8080)
            else:
                # 🚀 Deployment (Service Account)
                print("Using service account credentials for deployment")
                credentials_info = load_credentials_from_env()
                self.creds = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=self.scopes
                )

            # 📡 Build Calendar API client
            self.service = build("calendar", "v3", credentials=self.creds)

            # ✅ Set calendar ID
            if not self.calendar_id:
                raise ValueError("GOOGLE_CALENDAR_ID environment variable not set")
            
            # Optional sanity check
            self.service.calendars().get(calendarId=self.calendar_id).execute()

            print("✅ Google Calendar client initialized.")
            return True

        except Exception as e:
            logger.error(f"[Credential Setup Error] {e}")
            print(f"[Credential Setup Error] {e}")
            return False

    def find_earliest_available_slot(self, duration: int = 30) -> datetime.datetime:
        """
        Find the earliest available time slot in the calendar between 8 AM and 9 PM JST.
        Searches across multiple days until an available slot is found.
        Time slots are checked in 15-minute increments (00, 15, 30, 45).

        Args:
            duration: Duration of the slot needed in minutes

        Returns:
            datetime object representing the start of the earliest available slot
        """
        now = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9)))

        def round_up_to_15_minutes(dt):
            """Round datetime up to the next 15-minute mark (00, 15, 30, 45)"""
            minute = dt.minute
            if minute % 15 == 0:
                return dt.replace(second=0, microsecond=0)
            next_quarter = ((minute // 15) + 1) * 15
            if next_quarter >= 60:
                return (dt + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            return dt.replace(minute=next_quarter, second=0, microsecond=0)

        # If current time is before 8 AM, start from 8 AM today
        if now.hour < self.business_hours_start:
            search_start = now.replace(
                hour=self.business_hours_start, minute=0, second=0, microsecond=0)
        # If current time is after 9 PM, start from 8 AM tomorrow
        elif now.hour >= self.business_hours_end:
            tomorrow = now + datetime.timedelta(days=1)
            search_start = tomorrow.replace(
                hour=self.business_hours_start, minute=0, second=0, microsecond=0)
        else:
            # Start from current time, rounded up to the next 15-minute mark
            search_start = round_up_to_15_minutes(now)

        # Look ahead for 30 days maximum
        search_end = search_start + datetime.timedelta(days=30)

        try:
            # Get busy periods for the next 30 days
            body = {
                "timeMin": search_start.isoformat(),
                "timeMax": search_end.isoformat(),
                "items": [{"id": self.calendar_id}],
                "timeZone": self.timezone
            }

            free_busy_query = self.service.freebusy().query(body=body).execute()
            busy_periods = free_busy_query["calendars"][self.calendar_id]["busy"]

            current_time = search_start
            slot_duration = datetime.timedelta(minutes=duration)

            while current_time < search_end:
                # Skip times outside business hours
                if current_time.hour < self.business_hours_start:
                    current_time = current_time.replace(
                        hour=self.business_hours_start, minute=0)
                    continue
                if current_time.hour >= self.business_hours_end:
                    tomorrow = current_time + datetime.timedelta(days=1)
                    current_time = tomorrow.replace(
                        hour=self.business_hours_start, minute=0)
                    continue

                slot_end = current_time + slot_duration
                # Skip if slot would end after business hours
                if slot_end.hour >= self.business_hours_end or (slot_end.hour == self.business_hours_end and slot_end.minute > 0):
                    tomorrow = current_time + datetime.timedelta(days=1)
                    current_time = tomorrow.replace(
                        hour=self.business_hours_start, minute=0)
                    continue

                is_free = True
                for period in busy_periods:
                    period_start = datetime.datetime.fromisoformat(
                        period["start"].replace('Z', '+00:00'))
                    period_end = datetime.datetime.fromisoformat(
                        period["end"].replace('Z', '+00:00'))

                    # Only consider it busy if the slot starts before a busy period ends
                    # AND the slot ends after a busy period starts
                    if (current_time < period_end and slot_end > period_start):
                        is_free = False
                        # Move to the end of this busy period, rounded up to next 15-minute mark
                        def round_up_to_15_minutes_inner(dt):
                            minute = dt.minute
                            if minute % 15 == 0:
                                return dt.replace(second=0, microsecond=0)
                            next_quarter = ((minute // 15) + 1) * 15
                            if next_quarter >= 60:
                                return (dt + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                            return dt.replace(minute=next_quarter, second=0, microsecond=0)
                        current_time = round_up_to_15_minutes_inner(period_end)
                        break

                if is_free:
                    return current_time

                # If we didn't find a slot, try the next 15-minute increment
                if not is_free:
                    continue  # Skip the increment since we already moved to period_end

                current_time += datetime.timedelta(minutes=15)

            # If no slot found within 30 days, raise an exception
            raise Exception("No available slots found in the next 30 days")

        except Exception as e:
            logger.error(f"Error finding available slot: {str(e)}")
            raise Exception(f"Could not find an available slot: {str(e)}")

    def schedule_reading_session(self, book_title: str, duration: int = 30) -> Dict:
        """
        Schedule a reading session in Google Calendar.

        Args:
            book_title: Title of the book to read
            duration: Duration of reading session in minutes
            preferred_time: Preferred time for the session (not used anymore)

        Returns:
            Dictionary containing success status and event details
        """
        # Check if calendar service is enabled and properly configured
        if not self.enabled or not self.service:
            return {
                'success': False,
                'error': 'Calendar service not available. Please check your Google Calendar configuration and credentials.'
            }
        
        try:
            # Find the earliest available slot within business hours
            try:
                start_time = self.find_earliest_available_slot(
                    duration)
                logger.info(f"Found available slot: {start_time}")
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

            end_time = start_time + \
                datetime.timedelta(minutes=duration)

            event = {
                'summary': f"📚 Reading: {book_title}",
                'description': f"Reading session for '{book_title}'\n\n"
                f"Duration: {duration} minutes\n"
                f"Scheduled via Noah AI Assistant",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'reminders': {
                    'useDefault': True
                }
            }

            # Try to create the event
            try:
                created_event = self.service.events().insert(
                    calendarId=self.calendar_id, body=event).execute()
                logger.info(f"Successfully created calendar event: {created_event['id']}")
            except Exception as calendar_error:
                logger.error(f"Failed to create calendar event: {str(calendar_error)}")
                raise calendar_error

            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'scheduled_time': start_time.strftime('%Y-%m-%d %H:%M'),
                'duration': duration
            }

        except Exception as e:
            logger.error(f"Error scheduling reading session: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to schedule reading session: {str(e)}"
            }

    def get_upcoming_reading_sessions(self, limit: int = 10) -> Dict:
        """Get upcoming reading sessions from calendar"""
        if not self.enabled or not self.setup_credentials():
            return {"success": False, "error": "Calendar service not available"}

        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime',
                q='Reading:'
            ).execute()

            events = events_result.get('items', [])

            sessions = []
            for event in events:
                start = event['start'].get(
                    'dateTime', event['start'].get('date'))
                sessions.append({
                    'summary': event['summary'],
                    'start_time': start,
                    'description': event.get('description', ''),
                    'link': event.get('htmlLink', '')
                })

            return {
                'success': True,
                'sessions': sessions
            }

        except Exception as e:
            logger.error(f"Error getting reading sessions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    calendar_service = CalendarService()
    print(calendar_service.schedule_reading_session("Three Body Problem", 15))
