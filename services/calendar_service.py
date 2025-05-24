# import os
# import datetime
# from typing import Dict
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build
# from dotenv import load_dotenv

# load_dotenv()

# SCOPES = ['https://www.googleapis.com/auth/calendar']

# class CalendarService:
#     def __init__(self):
#         self.creds = None
#         self.service = None
#         self.setup_credentials()

#     def setup_credentials(self):
#         """Set up Google Calendar API credentials."""
#         if os.path.exists('token.json'):
#             self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)

#         if not self.creds or not self.creds.valid:
#             if self.creds and self.creds.expired and self.creds.refresh_token:
#                 self.creds.refresh(Request())
#             else:
#                 flow = InstalledAppFlow.from_client_secrets_file(
#                     os.getenv('GOOGLE_CALENDAR_CREDENTIALS_FILE'), SCOPES)
#                 self.creds = flow.run_local_server(port=0)

#             with open('token.json', 'w') as token:
#                 token.write(self.creds.to_json())

#         self.service = build('calendar', 'v3', credentials=self.creds)

#     def schedule_reading_time(self, book_details: Dict, duration_minutes: int = 30) -> Dict:
#         """
#         Schedule a reading session in Google Calendar.

#         Args:
#             book_details: Dictionary containing book information
#             duration_minutes: Duration of reading session in minutes

#         Returns:
#             Dictionary containing event details
#         """
#         # Find the next available time slot
#         now = datetime.datetime.utcnow()
#         start_time = now + datetime.timedelta(hours=1)  # Start from next hour
#         start_time = start_time.replace(minute=0, second=0, microsecond=0)  # Round to hour

#         end_time = start_time + datetime.timedelta(minutes=duration_minutes)

#         event = {
#             'summary': f"Reading: {book_details['title']}",
#             'description': f"Reading session for '{book_details['title']}' by {book_details['author']}\n\n"
#                          f"Book Link: {book_details['link']}\n"
#                          f"Pages: {book_details.get('num_pages', 'N/A')}",
#             'start': {
#                 'dateTime': start_time.isoformat(),
#                 'timeZone': 'UTC',
#             },
#             'end': {
#                 'dateTime': end_time.isoformat(),
#                 'timeZone': 'UTC',
#             },
#             'reminders': {
#                 'useDefault': True
#             }
#         }

#         try:
#             event = self.service.events().insert(calendarId='primary', body=event).execute()
#             return {
#                 'status': 'success',
#                 'event_id': event['id'],
#                 'link': event['htmlLink'],
#                 'start_time': start_time.isoformat(),
#                 'end_time': end_time.isoformat()
#             }
#         except Exception as e:
#             print(f"Error scheduling reading time: {str(e)}")
#             return {
#                 'status': 'error',
#                 'message': str(e)
#             }
