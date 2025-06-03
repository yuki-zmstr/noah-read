"""
Calendar Service for CapyRead - Handles Google Calendar integration for scheduling reading sessions
"""

import os
import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CalendarService:
    """Service for scheduling reading sessions in Google Calendar"""
    
    def __init__(self):
        self.enabled = False
        try:
            # Only import Google Calendar dependencies if they're available
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            self.creds = None
            self.service = None
            self.scopes = ['https://www.googleapis.com/auth/calendar']
            self.enabled = True
            logger.info("Google Calendar service initialized successfully")
        except ImportError:
            logger.warning("Google Calendar dependencies not available. Calendar features disabled.")
    
    def setup_credentials(self):
        """Set up Google Calendar API credentials."""
        if not self.enabled:
            return False
            
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.scopes)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    credentials_file = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_FILE', 'google_credentials.json')
                    if not os.path.exists(credentials_file):
                        logger.error(f"Google credentials file not found: {credentials_file}")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.scopes)
                    self.creds = flow.run_local_server(port=0)

                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Google Calendar credentials: {str(e)}")
            return False

    def schedule_reading_session(self, book_title: str, duration_minutes: int = 30, 
                               preferred_time: Optional[str] = None) -> Dict:
        """
        Schedule a reading session in Google Calendar.

        Args:
            book_title: Title of the book to read
            duration_minutes: Duration of reading session in minutes
            preferred_time: Preferred time for the session (optional)

        Returns:
            Dictionary containing success status and event details
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Google Calendar integration not available. Please install google-auth-oauthlib, google-auth-httplib2, and google-api-python-client."
            }
        
        if not self.setup_credentials():
            return {
                "success": False,
                "error": "Failed to set up Google Calendar credentials. Please check your credentials file."
            }

        try:
            # Calculate start and end times
            now = datetime.datetime.now()
            
            if preferred_time:
                # Try to parse preferred time (simplified parsing for demo)
                try:
                    # Handle formats like "2pm", "14:00", "tomorrow 3pm"
                    if "tomorrow" in preferred_time.lower():
                        start_time = now.replace(hour=14, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
                    elif "pm" in preferred_time.lower():
                        hour = int(preferred_time.lower().replace("pm", "").strip())
                        if hour != 12:
                            hour += 12
                        start_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                        if start_time <= now:
                            start_time += datetime.timedelta(days=1)
                    else:
                        # Default to next available hour
                        start_time = now + datetime.timedelta(hours=1)
                        start_time = start_time.replace(minute=0, second=0, microsecond=0)
                except:
                    # Fallback to next hour
                    start_time = now + datetime.timedelta(hours=1)
                    start_time = start_time.replace(minute=0, second=0, microsecond=0)
            else:
                # Default to next hour
                start_time = now + datetime.timedelta(hours=1)
                start_time = start_time.replace(minute=0, second=0, microsecond=0)

            end_time = start_time + datetime.timedelta(minutes=duration_minutes)

            event = {
                'summary': f"📚 Reading: {book_title}",
                'description': f"Reading session for '{book_title}'\n\n"
                             f"Duration: {duration_minutes} minutes\n"
                             f"Scheduled via CapyRead AI Assistant",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': True
                }
            }

            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'scheduled_time': start_time.strftime('%Y-%m-%d %H:%M'),
                'duration': duration_minutes
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
                calendarId='primary',
                timeMin=now,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime',
                q='Reading:'
            ).execute()
            
            events = events_result.get('items', [])
            
            sessions = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
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
