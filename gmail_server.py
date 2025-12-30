import os
import base64
import logging
import asyncio
from typing import Any
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gmail-mcp-server")

# Scopes required for the Gmail API
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose"
]

# Module-level service cache
_cached_service = None

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

async def retry_with_backoff(func, max_retries=3):
    """
    Retry a function with exponential backoff for transient errors.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts

    Returns:
        Result of the function call

    Raises:
        HttpError: If non-transient error or max retries exceeded
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except HttpError as e:
            # Retry on server errors (500, 503)
            if e.resp.status in [500, 503] and attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Transient error (status {e.resp.status}), retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                # Don't retry on client errors or if max retries reached
                raise

def get_gmail_service():
    """Authenticates and returns the Gmail API service."""
    global _cached_service

    if _cached_service is not None:
        logger.debug("Using cached Gmail service")
        return _cached_service

    logger.info("Initializing new Gmail service")
    creds = None
    # The file token.json stores the user's access and refresh tokens
    token_path = os.path.join(SCRIPT_DIR, "token.json")
    if os.path.exists(token_path):
        logger.debug("Loading credentials from token.json")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired access token")
            creds.refresh(Request())
        else:
            credentials_path = os.path.join(SCRIPT_DIR, "credentials.json")
            if not os.path.exists(credentials_path):
                logger.error(f"credentials.json file not found at {credentials_path}")
                raise FileNotFoundError("credentials.json not found. Please follow the setup guide to obtain it.")

            logger.info("Starting OAuth 2.0 authorization flow")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        logger.debug("Saving credentials to token.json")
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    logger.info("Gmail service initialized successfully")
    _cached_service = build("gmail", "v1", credentials=creds)
    return _cached_service

async def handle_get_unread_emails(max_results: int = 10) -> list[dict[str, Any]]:
    """
    Retrieve unread emails from the Gmail account.

    Args:
        max_results: Maximum number of unread emails to retrieve (default 10).

    Returns:
        A list of dictionaries containing sender, subject, snippet, and ID.
    """
    # Input validation
    if not isinstance(max_results, int) or max_results < 1:
        logger.error(f"Invalid max_results: {max_results}")
        return [{"error": "max_results must be a positive integer"}]

    if max_results > 500:
        logger.warning(f"max_results {max_results} exceeds Gmail API limit, capping at 500")
        max_results = 500

    logger.info(f"Fetching up to {max_results} unread emails")
    try:
        # Run blocking service initialization in thread pool
        service = await asyncio.to_thread(get_gmail_service)
        logger.debug("Gmail service ready")

        # Run blocking API call in thread pool with retry logic
        results = await retry_with_backoff(
            lambda: asyncio.to_thread(
                lambda: service.users().messages().list(
                    userId='me', q='is:unread', maxResults=max_results
                ).execute()
            )
        )
        logger.debug(f"API returned {len(results.get('messages', []))} messages")
        messages = results.get('messages', [])

        # Handle case where no unread emails exist
        if not messages:
            logger.info("No unread emails found")
            return []

        unread_emails = []
        for msg in messages:
            # Run blocking message fetch in thread pool with retry logic
            msg_data = await retry_with_backoff(
                lambda m=msg: asyncio.to_thread(
                    lambda: service.users().messages().get(userId='me', id=m['id']).execute()
                )
            )

            # Validate message data structure
            payload = msg_data.get('payload')
            if not payload:
                logger.warning(f"Message {msg['id']} has no payload, skipping")
                continue

            headers = payload.get('headers', [])
            if not headers:
                logger.warning(f"Message {msg['id']} has no headers, skipping")
                continue

            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')

            unread_emails.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "from": sender,
                "subject": subject,
                "snippet": msg_data.get('snippet', '')
            })

        logger.info(f"Successfully processed {len(unread_emails)} unread emails")
        return unread_emails
    except HttpError as e:
        if e.resp.status == 404:
            logger.error(f"Resource not found: {e}")
            return [{"error": "Email or thread not found", "code": 404}]
        elif e.resp.status == 429:
            logger.error(f"Rate limit exceeded: {e}")
            return [{"error": "Gmail API rate limit exceeded. Try again later.", "code": 429}]
        elif e.resp.status == 403:
            logger.error(f"Access denied: {e}")
            return [{"error": "Access denied. Check API credentials and permissions.", "code": 403}]
        elif e.resp.status >= 500:
            logger.error(f"Gmail API server error: {e}", exc_info=True)
            return [{"error": f"Gmail server error (status {e.resp.status}). Try again later.", "code": e.resp.status}]
        else:
            logger.error(f"Gmail API error: {e}", exc_info=True)
            return [{"error": f"Gmail API error: {str(e)}", "code": e.resp.status}]
    except RefreshError as e:
        logger.error(f"Token refresh failed: {e}")
        return [{"error": "Authentication token expired. Delete token.json and re-authorize.", "code": "auth_expired"}]
    except FileNotFoundError as e:
        logger.error(f"Credentials file missing: {e}")
        return [{"error": "credentials.json not found. See README for setup instructions.", "code": "missing_creds"}]
    except Exception as e:
        logger.error(f"Unexpected error fetching unread emails: {e}", exc_info=True)
        return [{"error": f"Unexpected error: {str(e)}"}]

async def handle_create_draft_reply(thread_id: str, reply_body: str) -> dict[str, Any]:
    """
    Create a draft reply to an existing email thread.

    Args:
        thread_id: The ID of the thread to reply to.
        reply_body: The content of the reply.

    Returns:
        A dictionary containing the draft ID and status.
    """
    # Input validation
    if not isinstance(thread_id, str) or not thread_id.strip():
        logger.error(f"Invalid thread_id: {thread_id}")
        return {"error": "thread_id must be a non-empty string"}

    if not isinstance(reply_body, str) or not reply_body.strip():
        logger.error(f"Invalid reply_body: empty or not a string")
        return {"error": "reply_body must be a non-empty string"}

    # Check reply body length (Gmail has ~100KB limit for message body)
    if len(reply_body.encode('utf-8')) > 102400:  # 100KB in bytes
        logger.error(f"Reply body too large: {len(reply_body.encode('utf-8'))} bytes")
        return {"error": "reply_body exceeds maximum size of 100KB"}

    logger.info(f"Creating draft reply for thread {thread_id}")
    try:
        # Run blocking service initialization in thread pool
        service = await asyncio.to_thread(get_gmail_service)
        logger.debug("Gmail service ready")

        # Get the original message to extract headers for threading
        logger.debug(f"Fetching thread {thread_id} to extract headers")
        thread = await retry_with_backoff(
            lambda: asyncio.to_thread(
                lambda: service.users().threads().get(userId='me', id=thread_id).execute()
            )
        )
        messages = thread.get('messages', [])
        if not messages:
            return {"error": "Thread not found or empty."}

        last_message = messages[-1]
        payload = last_message.get('payload')
        if not payload:
            logger.warning(f"Thread {thread_id} has message without payload")
            return {"error": "Email message has incomplete data"}

        headers = payload.get('headers', [])
        if not headers:
            logger.warning(f"Thread {thread_id} has no headers")
            return {"error": "Email message has no headers"}

        # Extract necessary headers for threading
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"

        message_id = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), None)
        to_address = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)

        # Validate required headers
        if not to_address:
            logger.error(f"Cannot determine recipient address for thread {thread_id}")
            return {"error": "Cannot determine recipient address from original email"}

        # Create the MIME message
        message = MIMEText(reply_body)
        message['to'] = to_address
        message['subject'] = subject

        # Only set threading headers if message_id is available
        if message_id:
            message['In-Reply-To'] = message_id
            message['References'] = message_id
        else:
            logger.warning(f"Thread {thread_id} has no Message-ID header, threading may be imperfect")

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        draft_body = {
            'message': {
                'threadId': thread_id,
                'raw': raw_message
            }
        }

        # Run blocking draft creation in thread pool with retry logic
        logger.debug("Creating draft in Gmail")
        draft = await retry_with_backoff(
            lambda: asyncio.to_thread(
                lambda: service.users().drafts().create(userId='me', body=draft_body).execute()
            )
        )
        logger.info(f"Successfully created draft {draft['id']} for thread {thread_id}")
        return {"status": "success", "draftId": draft['id'], "threadId": thread_id}

    except HttpError as e:
        if e.resp.status == 404:
            logger.error(f"Thread not found: {e}")
            return {"error": f"Thread {thread_id} not found", "code": 404}
        elif e.resp.status == 429:
            logger.error(f"Rate limit exceeded: {e}")
            return {"error": "Gmail API rate limit exceeded. Try again later.", "code": 429}
        elif e.resp.status == 403:
            logger.error(f"Access denied: {e}")
            return {"error": "Access denied. Check API credentials and permissions.", "code": 403}
        elif e.resp.status >= 500:
            logger.error(f"Gmail API server error: {e}", exc_info=True)
            return {"error": f"Gmail server error (status {e.resp.status}). Try again later.", "code": e.resp.status}
        else:
            logger.error(f"Gmail API error creating draft: {e}", exc_info=True)
            return {"error": f"Gmail API error: {str(e)}", "code": e.resp.status}
    except RefreshError as e:
        logger.error(f"Token refresh failed: {e}")
        return {"error": "Authentication token expired. Delete token.json and re-authorize.", "code": "auth_expired"}
    except FileNotFoundError as e:
        logger.error(f"Credentials file missing: {e}")
        return {"error": "credentials.json not found. See README for setup instructions.", "code": "missing_creds"}
    except Exception as e:
        logger.error(f"Unexpected error creating draft reply: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Gmail MCP server")

    # Create server instance
    server = Server("gmail")

    # Register list_tools handler
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_unread_emails",
                description="Retrieve unread emails from the Gmail account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of unread emails to retrieve (default 10, max 500)",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="create_draft_reply",
                description="Create a draft reply to an existing email thread",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "string",
                            "description": "The ID of the thread to reply to"
                        },
                        "reply_body": {
                            "type": "string",
                            "description": "The content of the reply"
                        }
                    },
                    "required": ["thread_id", "reply_body"]
                }
            )
        ]

    # Register call_tool handler
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls from the MCP client."""
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "get_unread_emails":
            max_results = arguments.get("max_results", 10)
            result = await handle_get_unread_emails(max_results)
            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "create_draft_reply":
            thread_id = arguments.get("thread_id", "")
            reply_body = arguments.get("reply_body", "")
            result = await handle_create_draft_reply(thread_id, reply_body)
            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    # Run the server
    logger.info("Server initialized, starting stdio transport")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
