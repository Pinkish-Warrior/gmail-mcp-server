import os
import base64
import logging
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gmail-mcp-server")

# Scopes required for the Gmail API
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose"
]

# Initialize FastMCP server
mcp = FastMCP("Gmail")

def get_gmail_service():
    """Authenticates and returns the Gmail API service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("credentials.json not found. Please follow the setup guide to obtain it.")
            
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

@mcp.tool()
async def get_unread_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve unread emails from the Gmail account.
    
    Args:
        max_results: Maximum number of unread emails to retrieve (default 10).
    
    Returns:
        A list of dictionaries containing sender, subject, snippet, and ID.
    """
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
        messages = results.get('messages', [])

        unread_emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            
            unread_emails.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "from": sender,
                "subject": subject,
                "snippet": msg_data.get('snippet', '')
            })
        
        return unread_emails
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        return [{"error": str(e)}]

@mcp.tool()
async def create_draft_reply(thread_id: str, reply_body: str) -> Dict[str, Any]:
    """
    Create a draft reply to an existing email thread.
    
    Args:
        thread_id: The ID of the thread to reply to.
        reply_body: The content of the reply.
    
    Returns:
        A dictionary containing the draft ID and status.
    """
    try:
        service = get_gmail_service()
        
        # Get the original message to extract headers for threading
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        if not messages:
            return {"error": "Thread not found or empty."}
        
        last_message = messages[-1]
        headers = last_message.get('payload', {}).get('headers', [])
        
        # Extract necessary headers for threading
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
            
        message_id = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), None)
        to_address = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)
        
        # Create the MIME message
        message = MIMEText(reply_body)
        message['to'] = to_address
        message['subject'] = subject
        message['In-Reply-To'] = message_id
        message['References'] = message_id
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        draft_body = {
            'message': {
                'threadId': thread_id,
                'raw': raw_message
            }
        }
        
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        return {"status": "success", "draftId": draft['id'], "threadId": thread_id}
        
    except Exception as e:
        logger.error(f"Error creating draft reply: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
