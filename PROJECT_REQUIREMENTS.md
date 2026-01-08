# Foundation Project Requirements: MCP Server

This document contains the original specifications for the Foundation Project as part of the Claude AI program.

## Project Overview

Building an end-to-end project is the best way to prepare for our programme. This foundation project is a simplified version of what you'll work on every week, so it's an excellent way for you to learn and for us to assess your readiness.

## Task

Build and deploy an MCP server that allows an AI assistant to read unread emails from a Gmail account and create draft replies.

## What You'll Need to Understand

1. **Model Context Protocol documentation**
   - How tools work as callable functions
   - MCP server patterns and best practices

2. **Example MCP servers**
   - Study expected patterns from existing implementations
   - Understand MCP SDK usage

3. **Gmail API setup**
   - Creating a Google Cloud project
   - Enabling the Gmail API
   - Configuring OAuth 2.0 authentication
   - Understanding Gmail API scopes:
     - `gmail.readonly` - For reading emails
     - `gmail.compose` - For creating drafts

## Required Components

### 1. MCP Server Implementation

Choose one of the following:

- **Python** with `mcp` SDK (recommended)
- **TypeScript** with `@modelcontextprotocol/sdk`

### 2. Required Tools

#### Tool 1: `get_unread_emails`

**Purpose:** Retrieve unread emails from the Gmail account

**Returns:**

- Sender information
- Subject line
- Body/snippet preview
- Email/thread ID (for replying)

**Parameters:**

- `max_results` (optional): Maximum number of emails to retrieve

#### Tool 2: `create_draft_reply`

**Purpose:** Create a draft reply within an existing email thread

**Accepts:**

- Original email/thread ID
- Reply body text

**Requirements:**

- Must create a correctly threaded draft reply
- Should set proper email headers (`In-Reply-To`, `References`)
- Should maintain thread context in Gmail

### 3. Working Demo with Claude Desktop

**Configuration:**

- Configure Claude Desktop to connect to your server locally
- Document the `claude_desktop_config.json` configuration
- Ensure server appears in Claude Desktop's MCP server list

**Demo Requirements:**

- Include example prompts showing:
  - Claude reading unread emails
  - Claude creating draft replies
- Provide screenshots demonstrating:
  - Claude Desktop with MCP server connected
  - Email retrieval in action
  - Draft reply creation
  - Gmail drafts folder showing created drafts

### 4. GitHub Repository

**Required Documentation:**

- README.md covering:
  - What the server does
  - Prerequisites
  - Setup instructions
  - How to run locally
  - Example usage
  - Troubleshooting
- Clear, concise explanations
- Step-by-step setup guide
- Screenshots of working implementation

**Required Files:**

- Source code (`.py` or `.ts`)
- Dependencies file (`requirements.txt` or `package.json`)
- Configuration examples
- `.gitignore` (exclude sensitive files like `token.json`, `credentials.json`)

## Submission

Submit your GitHub repository link via the project submission form.

## Stretch Goal (Optional)

Enhance your server by pulling in external context to help the AI write better replies.

**Examples:**

- Email style guide from Google Docs
- Reply templates from Notion
- Files from a local knowledge base
- Company-specific writing guidelines

**Implementation Ideas:**

- Add a tool to fetch style guides
- Integrate with external APIs (Google Docs, Notion)
- Use MCP Resources to expose style guides
- Read local markdown files with templates

**Benefits:**

- Demonstrates advanced MCP features
- Shows integration capabilities
- Provides more contextual, styled responses

## Assessment Criteria

The foundation project demonstrates:

1. **Technical Implementation**
   - Correct use of MCP SDK
   - Proper Gmail API integration
   - Secure OAuth 2.0 authentication
   - Error handling and retry logic

2. **Code Quality**
   - Clean, readable code
   - Proper async/await patterns
   - Comprehensive error handling
   - Good logging practices

3. **Documentation**
   - Clear README with setup instructions
   - Example usage with screenshots
   - Configuration documentation
   - Troubleshooting guidance

4. **Working Demo**
   - Successfully retrieves emails
   - Creates properly threaded drafts
   - Works with Claude Desktop
   - Visual proof via screenshots

5. **Best Practices**
   - Sensitive data excluded from repository
   - Proper .gitignore configuration
   - Version control best practices
   - Professional repository structure

## Success Criteria

Your project is complete when:

- ✅ MCP server runs without errors
- ✅ Both tools (`get_unread_emails` and `create_draft_reply`) work correctly
- ✅ OAuth 2.0 authentication flow completes successfully
- ✅ Claude Desktop connects to your server
- ✅ Screenshots demonstrate working functionality
- ✅ README provides clear setup instructions
- ✅ Repository is clean and professional
- ✅ No sensitive credentials in repository

## Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [MCP Example Servers](https://github.com/modelcontextprotocol)

---

**Project Status:** ✅ Completed

**Implementation:** Python with MCP SDK
**Date Completed:** January 2026
