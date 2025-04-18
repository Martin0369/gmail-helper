import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import config
from datetime import datetime

class DriveService:
    def __init__(self):
        self.service = self._get_drive_service()
        
    def _get_drive_service(self):
        """Initialize Google Drive API service."""
        creds = None
        # Token file stores the user's access and refresh tokens
        if os.path.exists('drive_token.pickle'):
            with open('drive_token.pickle', 'rb') as token:
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
                    config.GOOGLE_APPLICATION_CREDENTIALS, config.DRIVE_SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('drive_token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                
        # Build the service with static discovery document
        return build('drive', 'v3', credentials=creds, cache_discovery=False)
    
    def get_or_create_folder(self, folder_name, parent_folder_id=None):
        """Get existing folder or create new one."""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            else:
                query += f" and '{config.DRIVE_FOLDER_ID}' in parents"
                
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            else:
                return self.create_folder(folder_name, parent_folder_id)
                
        except Exception as e:
            print(f"Error getting/creating folder: {str(e)}")
            return None
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a new folder in Google Drive."""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id if parent_folder_id else config.DRIVE_FOLDER_ID]
            }
            
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            return None
    
    def upload_file(self, file_data, filename, mime_type, folder_id):
        """Upload file to Google Drive."""
        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            fh = io.BytesIO(file_data)
            media = MediaIoBaseUpload(
                fh,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_link': file.get('webViewLink')
            }
            
        except Exception as e:
            print(f"Error uploading file to Drive: {str(e)}")
            return None
    
    def update_file_metadata(self, file_id, metadata):
        """Update file metadata in Google Drive."""
        try:
            file_metadata = {
                'description': str(metadata),
                'properties': {
                    'document_type': metadata.get('document_type', ''),
                    'processed_date': metadata.get('processed_date', ''),
                    'source_email': metadata.get('source_email', '')
                }
            }
            
            self.service.files().update(
                fileId=file_id,
                body=file_metadata,
                fields='id, name, description, properties'
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error updating file metadata: {str(e)}")
            return False 