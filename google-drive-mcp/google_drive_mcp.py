"""
Author: Shashank Kumar (stellarshank.dev@gmail.com)
Date: November 2025
Project: Google Drive FastMCP Integration

Description:
-------------
This script provides an MCP (Model Context Protocol) tool that integrates with Google Drive
for listing files, uploading files, and creating folders programmatically. It uses the Google API
Python client, OAuth2 credentials, and FastMCP to expose these functionalities as tools for
automation or AI integrations.

Key Features:
--------------
1. OAuth2-based authentication and token storage
2. Upload files to Drive
3. List Drive files with webView links
4. Create Drive folders
5. Designed for integration with AI or automation systems using FastMCP
"""

import os
import pickle
from typing import Optional

from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# Scopes define what access the app will request — here, permission to manage files created by this app.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    """Initialize and return Google Drive API service instance with OAuth2 credentials."""
    token_path = os.path.join(os.environ.get('USERPROFILE', ''), '.google_drive_token.pickle')
    creds = None

    # Load saved user credentials from disk (if available)
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If credentials are invalid or missing, prompt the user to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(script_dir, 'credentials.json')
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    # Return Google Drive API client
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


# Initialize the FastMCP instance for registering Drive tools
mcp = FastMCP("google-drive")


@mcp.tool()
def list_drive_files(page_size: int = 10) -> str:
    """
    List recent files in Google Drive.

    Args:
        page_size: Number of files to return (max 100).

    Returns:
        Formatted string listing file names, IDs, and webView links.
    """
    try:
        if page_size > 100:
            page_size = 100

        service = get_drive_service()
        results = service.files().list(
            pageSize=page_size,
            fields="files(id, name, mimeType, webViewLink)"
        ).execute()

        files = results.get('files', [])
        if not files:
            return "No files found in Google Drive."

        output = f"Found {len(files)} files:\n\n"
        for idx, file in enumerate(files, 1):
            output += f"{idx}. {file['name']}\n"
            output += f"   ID: {file['id']}\n"
            if 'webViewLink' in file:
                output += f"   Link: {file['webViewLink']}\n"
            output += "\n"

        return output
    except Exception as e:
        return f"Error listing files: {str(e)}"


@mcp.tool()
def upload_to_drive(file_path: str, folder_id: str = "") -> str:
    """
    Upload a file to Google Drive.

    Args:
        file_path: Path to the file to upload.
        folder_id: Optional folder ID to upload into.

    Returns:
        Confirmation message with file name and shareable link.
    """
    try:
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        service = get_drive_service()
        file_metadata = {'name': os.path.basename(file_path)}

        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()

        return f"✓ File uploaded!\nName: {file['name']}\nLink: {file.get('webViewLink', 'N/A')}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"


@mcp.tool()
def create_drive_folder(folder_name: str, parent_id: str = "") -> str:
    """
    Create a folder in Google Drive.

    Args:
        folder_name: Name of the folder to create.
        parent_id: Optional parent folder ID to nest inside.

    Returns:
        Confirmation message with folder name and ID.
    """
    try:
        service = get_drive_service()
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = service.files().create(
            body=file_metadata,
            fields='id, name'
        ).execute()

        return f"✓ Folder created!\nName: {folder['name']}\nID: {folder['id']}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"
