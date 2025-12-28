"""
Google Drive Cloud Backup for Clinic App
Handles authentication and file upload to Google Drive
"""

import os
import json
import pickle
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Default email for the app
DEFAULT_EMAIL = 'zainyousaf099@gmail.com'

def get_credentials_path():
    """Get the path where credentials are stored"""
    # Store in user's app data folder
    app_data = os.path.join(os.path.expanduser('~'), '.clinic_app')
    if not os.path.exists(app_data):
        os.makedirs(app_data)
    return app_data

def get_token_path():
    """Get the path to the token file"""
    return os.path.join(get_credentials_path(), 'gdrive_token.pickle')

def get_client_secrets_path():
    """Get the path to client secrets file"""
    return os.path.join(get_credentials_path(), 'client_secrets.json')

def check_auth_status():
    """Check if user is authenticated with Google Drive"""
    token_path = get_token_path()
    
    if os.path.exists(token_path):
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            
            if creds and creds.valid:
                return {
                    'authenticated': True,
                    'email': getattr(creds, 'client_id', DEFAULT_EMAIL),
                    'message': 'Connected to Google Drive'
                }
            elif creds and creds.expired and creds.refresh_token:
                # Try to refresh
                creds.refresh(Request())
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                return {
                    'authenticated': True,
                    'email': DEFAULT_EMAIL,
                    'message': 'Connection refreshed'
                }
        except Exception as e:
            pass
    
    return {
        'authenticated': False,
        'email': None,
        'message': 'Not connected to Google Drive'
    }

def get_drive_service():
    """Get authenticated Google Drive service"""
    creds = None
    token_path = get_token_path()
    
    # Load existing credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, need to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None
    
    # Save refreshed credentials
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def authenticate_gdrive(auth_code=None):
    """
    Authenticate with Google Drive using OAuth2
    Returns auth URL if no code provided, or completes auth if code provided
    """
    client_secrets_path = get_client_secrets_path()
    
    # Check if client secrets exist
    if not os.path.exists(client_secrets_path):
        return {
            'success': False,
            'error': 'Google Drive not configured. Please set up client_secrets.json',
            'needs_setup': True
        }
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path, 
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        
        if auth_code:
            # Complete authentication with the code
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save credentials
            token_path = get_token_path()
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            
            return {
                'success': True,
                'authenticated': True,
                'message': 'Successfully connected to Google Drive!'
            }
        else:
            # Generate auth URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            return {
                'success': True,
                'auth_url': auth_url,
                'message': 'Please visit the URL and enter the authorization code'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def upload_to_gdrive(file_path, folder_name='Clinic_Backups'):
    """
    Upload a file to Google Drive
    
    Args:
        file_path: Path to the file to upload
        folder_name: Name of the folder to create/use in Drive
    
    Returns:
        dict with success status and file info
    """
    try:
        service = get_drive_service()
        
        if not service:
            return {
                'success': False,
                'error': 'Not authenticated with Google Drive',
                'needs_auth': True
            }
        
        # Check if folder exists, create if not
        folder_id = get_or_create_folder(service, folder_name)
        
        if not folder_id:
            return {
                'success': False,
                'error': 'Could not create backup folder in Drive'
            }
        
        # Prepare file metadata
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"clinic_backup_{timestamp}.sqlite3"
        
        file_metadata = {
            'name': backup_name,
            'parents': [folder_id]
        }
        
        # Upload file
        media = MediaFileUpload(
            file_path,
            mimetype='application/x-sqlite3',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return {
            'success': True,
            'file_id': file.get('id'),
            'file_name': file.get('name'),
            'web_link': file.get('webViewLink'),
            'message': f'Backup uploaded successfully: {backup_name}'
        }
        
    except HttpError as e:
        return {
            'success': False,
            'error': f'Google Drive API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_or_create_folder(service, folder_name):
    """Get existing folder or create new one in Drive"""
    try:
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
        
    except Exception as e:
        print(f"Error creating folder: {e}")
        return None

def list_backups():
    """List all backups in the Clinic_Backups folder"""
    try:
        service = get_drive_service()
        
        if not service:
            return {
                'success': False,
                'error': 'Not authenticated',
                'needs_auth': True
            }
        
        # Find backup folder
        query = "name='Clinic_Backups' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        folders = results.get('files', [])
        
        if not folders:
            return {
                'success': True,
                'backups': [],
                'message': 'No backups found'
            }
        
        folder_id = folders[0]['id']
        
        # List files in folder
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, createdTime, size)',
            orderBy='createdTime desc'
        ).execute()
        
        backups = results.get('files', [])
        
        return {
            'success': True,
            'backups': backups,
            'count': len(backups)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def download_backup(file_id, destination_path):
    """Download a backup from Google Drive"""
    try:
        service = get_drive_service()
        
        if not service:
            return {
                'success': False,
                'error': 'Not authenticated'
            }
        
        request = service.files().get_media(fileId=file_id)
        
        with open(destination_path, 'wb') as f:
            downloader = request.execute()
            f.write(downloader)
        
        return {
            'success': True,
            'message': 'Backup downloaded successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def disconnect_gdrive():
    """Disconnect from Google Drive (remove stored credentials)"""
    token_path = get_token_path()
    
    try:
        if os.path.exists(token_path):
            os.remove(token_path)
        
        return {
            'success': True,
            'message': 'Disconnected from Google Drive'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def setup_client_secrets(client_id, client_secret):
    """Save Google OAuth client credentials"""
    client_secrets = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    
    secrets_path = get_client_secrets_path()
    
    try:
        with open(secrets_path, 'w') as f:
            json.dump(client_secrets, f)
        
        return {
            'success': True,
            'message': 'Google Drive credentials saved'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_last_backup_date():
    """Get the date of the last local backup"""
    backup_folder = os.path.join(get_credentials_path(), 'local_backups')
    
    if not os.path.exists(backup_folder):
        return None
    
    backups = [f for f in os.listdir(backup_folder) if f.endswith('.sqlite3')]
    
    if not backups:
        return None
    
    # Get most recent
    backups.sort(reverse=True)
    latest = backups[0]
    
    # Parse date from filename
    try:
        date_str = latest.replace('clinic_backup_', '').replace('.sqlite3', '')
        return datetime.strptime(date_str.split('_')[0], '%Y%m%d')
    except:
        return None

def should_backup_today():
    """Check if we should create a backup today"""
    last_backup = get_last_backup_date()
    
    if not last_backup:
        return True
    
    today = datetime.now().date()
    return last_backup.date() < today

def create_local_backup(db_path):
    """Create a local backup of the database"""
    import shutil
    
    backup_folder = os.path.join(get_credentials_path(), 'local_backups')
    
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"clinic_backup_{timestamp}.sqlite3"
    backup_path = os.path.join(backup_folder, backup_name)
    
    try:
        shutil.copy2(db_path, backup_path)
        
        # Keep only last 7 local backups
        cleanup_old_backups(backup_folder, keep=7)
        
        return {
            'success': True,
            'backup_path': backup_path,
            'backup_name': backup_name
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_old_backups(folder, keep=7):
    """Keep only the most recent backups"""
    try:
        backups = [f for f in os.listdir(folder) if f.endswith('.sqlite3')]
        backups.sort(reverse=True)
        
        # Delete old backups
        for old_backup in backups[keep:]:
            os.remove(os.path.join(folder, old_backup))
    except:
        pass
