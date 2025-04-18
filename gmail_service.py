import os
import base64
import email
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.discovery_cache import DISCOVERY_DOC_MAX_AGE
import config

class GmailService:
    def __init__(self):
        self.service = self._get_gmail_service()
        
    def _get_gmail_service(self):
        """Initialize Gmail API service."""
        creds = None
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                try:
                    creds = pickle.load(token)
                except:
                    pass
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
                    
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GMAIL_CREDENTIALS, config.GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                
        # Build the service with static discovery document
        return build('gmail', 'v1', credentials=creds, cache_discovery=False)
    
    def get_emails_with_attachments(self, days_back=config.DAYS_TO_SEARCH):
        """Fetch emails with attachments from the last X days."""
        try:
            # Calculate date range
            date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f'{config.EMAIL_SEARCH_QUERY} after:{date_after}'
            
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            emails_with_attachments = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                if self._has_attachments(msg):
                    email_data = self._process_email(msg)
                    if email_data:
                        emails_with_attachments.append(email_data)
                        
            return emails_with_attachments
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def _has_attachments(self, message):
        """Check if email has attachments."""
        if 'parts' not in message['payload']:
            return False
            
        for part in message['payload']['parts']:
            if part.get('filename'):
                return True
        return False
    
    def _process_email(self, message):
        """Process email and extract relevant information."""
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            attachments = []
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename'):
                        attachment = {
                            'id': part['body'].get('attachmentId'),
                            'filename': part['filename'],
                            'mimeType': part['mimeType']
                        }
                        attachments.append(attachment)
            
            return {
                'message_id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'attachments': attachments
            }
            
        except Exception as e:
            print(f"Error processing email: {str(e)}")
            return None
    
    def download_attachment(self, message_id, attachment_id):
        """Download attachment from Gmail."""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            return file_data
            
        except Exception as e:
            print(f"Error downloading attachment: {str(e)}")
            return None 