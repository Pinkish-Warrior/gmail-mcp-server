# Gmail Model Context Protocol (MCP) Server

This project implements a Model Context Protocol (MCP) server in Python, enabling an AI assistant (such as Claude Desktop) to interact with a user's Gmail account. The server exposes two primary tools: one to read unread emails and another to create draft replies, facilitating an end-to-end email management workflow for the AI.

## Features

*   **`get_unread_emails`**: Retrieves a list of unread emails, providing the sender, subject, snippet, and the necessary thread ID for replying.
*   **`create_draft_reply`**: Creates a draft reply within an existing email thread, ensuring correct threading by setting the `ThreadId` and appropriate email headers (`In-Reply-To`, `References`).
*   **Secure Authentication**: Uses the official Google API Python client with OAuth 2.0 for desktop applications, storing credentials securely in a local `token.json` file after the initial authorization.

## Prerequisites

To run this server, you will need:

1.  **Python 3.10+**
2.  **A Google Account with Gmail enabled.**
3.  **A Google Cloud Project** with the **Gmail API** enabled.
4.  **OAuth 2.0 Client ID** for a **Desktop App** from the Google Cloud Console.

## Setup Guide

### 1. Clone the Repository and Install Dependencies

```bash
git clone <YOUR_REPO_URL>
cd gmail-mcp-server
pip install -r requirements.txt
```

### 2. Configure Gmail API Credentials

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Ensure the correct project is selected and the **Gmail API** is enabled.
3.  Navigate to **APIs & Services** > **Credentials**.
4.  Click **+ Create Credentials** > **OAuth client ID**.
5.  Select **Application type** as **Desktop app**.
6.  Give it a name (e.g., "Gmail MCP Server").
7.  Click **Create** and then **Download JSON**.
8.  Rename the downloaded file to `credentials.json` and place it in the root directory of this project (`gmail-mcp-server/`).

### 3. Run the Server and Authorize Access

The first time you run the server, it will initiate the OAuth 2.0 flow to authorize access to your Gmail account.

```bash
python gmail_server.py
```

1.  A browser window will open, prompting you to log in to your Google Account and grant the necessary permissions (`gmail.readonly` and `gmail.compose`).
2.  After successful authorization, a `token.json` file will be created in the project directory. This file securely stores your access and refresh tokens, allowing the server to run without re-authorization until the token expires or is revoked.

### 4. Configure Claude Desktop

1.  Ensure the MCP server is running in your terminal.
2.  Locate your Claude Desktop configuration file.
    *   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    *   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
3.  Add the following entry to the `mcpServers` section, replacing `/path/to/your/project` with the absolute path to your `gmail_server.py` file:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["/path/to/your/project/gmail-mcp-server/gmail_server.py"]
    }
  }
}
```

4.  Restart Claude Desktop. The AI assistant will now have access to the `Gmail` server and its tools.

## Example Usage with Claude Desktop

Once configured, you can use prompts like the following:

| Prompt | Expected AI Action |
| :--- | :--- |
| "Do I have any unread emails? If so, list the sender and subject of the first three." | Calls `get_unread_emails` and summarizes the results. |
| "Draft a reply to the email from [Sender Name] with the subject [Subject] saying 'Thank you for your message. I will get back to you by the end of the day.'" | Calls `get_unread_emails` to find the thread ID, then calls `create_draft_reply` with the ID and the specified body. |

## Stretch Goal: Enhancing Replies with External Context

To implement the stretch goal, you can modify the `create_draft_reply` function to first retrieve context from an external source (e.g., a local Markdown file for a style guide or a simple API for templates) and then pass that context to the LLM as part of the prompt or as an additional resource.

For example, you could add a local file `style_guide.md` and read its content before calling the LLM to generate the reply body.

```python
# Example of reading a local style guide
with open("style_guide.md", "r") as f:
    style_guide = f.read()

# You would then pass this to the LLM to influence the reply_body generation
# (This part is handled by the LLM client, not the MCP server itself)
```
