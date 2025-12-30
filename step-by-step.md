# Gmail MCP Server - Final Setup Steps

## Current Status

**Date**: 2025-12-30

**What's Working**:
- ✅ Server successfully rewritten with standard MCP SDK
- ✅ Server connects to Claude Desktop without timeout
- ✅ Both tools registered: `get_unread_emails`, `create_draft_reply`
- ✅ OAuth flow initiates correctly
- ✅ credentials.json is valid and properly configured

**What Needs to Be Done**:
- ⚠️ Configure OAuth consent screen in Google Cloud Console
- ⚠️ Add yourself as a test user
- ⚠️ Complete first OAuth authorization

**Current Error**: `Error 403: access_denied` - App needs OAuth consent screen configured

---

## Step-by-Step: Configure OAuth Consent Screen

### Step 1: Open Google Cloud Console

1. Open your browser
2. Go to: <https://console.cloud.google.com/apis/credentials/consent>
3. Make sure project **marine-fusion-482815-b9** is selected (check top left dropdown)

### Step 2: Configure OAuth Consent Screen

1. If you see "Configure Consent Screen" button, click it
2. **Choose User Type**:
   - Select **External** (unless you have Google Workspace, then choose Internal)
   - Click **CREATE**

### Step 3: OAuth Consent Screen Settings

1. **App information** section:
   - **App name**: `Gmail MCP Server`
   - **User support email**: Select your email from dropdown

2. **App domain** section (optional):
   - Leave blank or skip

3. **Developer contact information**:
   - **Email addresses**: Enter your email

4. Click **SAVE AND CONTINUE**

### Step 4: Configure Scopes

1. On the "Scopes" page, click **ADD OR REMOVE SCOPES**
2. In the filter box, search for: `gmail`
3. Check these two scopes:
   - ✅ `.../auth/gmail.readonly` - "Read all Gmail messages"
   - ✅ `.../auth/gmail.compose` - "Manage drafts"
4. Click **UPDATE** at the bottom
5. Verify both scopes appear in the table
6. Click **SAVE AND CONTINUE**

### Step 5: Add Test Users (CRITICAL)

1. On the "Test users" page, click **+ ADD USERS**
2. Enter your Gmail email address (the one you'll authorize with)
3. Click **ADD**
4. Verify your email appears in the test users list
5. Click **SAVE AND CONTINUE**

### Step 6: Review and Finish

1. Review the summary page
2. Click **BACK TO DASHBOARD**
3. **Important**: Verify "Publishing status" shows **Testing**
   - Do NOT publish to production
   - Stay in "Testing" mode

---

## Step 7: Test in Claude Desktop

1. **Open Claude Desktop** (should already be running)
2. **Start a new conversation**
3. Look for the 🔌 icon at the bottom - should show "gmail" server connected
4. **Type**: `"Check my unread emails"`

### Expected Flow

1. **Browser opens** automatically with Google OAuth screen
2. **Select your account** (must be the test user you added)
3. **Warning screen** may appear saying "Google hasn't verified this app"
   - Click **Continue** (safe - it's your own app)
4. **Grant permissions** screen shows the two Gmail scopes
   - Click **Allow**
5. **Browser shows**: "The authentication flow has completed"
6. **Claude Desktop**: Should show your unread emails!

### If You See Errors

**Error: "access_denied"**
- Go back to Step 5 and verify your email is added as a test user
- Make sure you're logging in with the same email

**Error: "redirect_uri_mismatch"**
- Credentials.json is correctly configured for localhost
- This shouldn't happen with current setup

**Browser doesn't open**
- Check Claude Desktop logs: `tail -f ~/Library/Logs/Claude/mcp-server-gmail.log`
- Restart Claude Desktop if needed

---

## After First Authorization

Once you successfully authorize:

1. A `token.json` file will be created in the project directory
2. Future requests won't need browser authorization
3. Token auto-refreshes when expired

### Test the Draft Reply Tool

After confirming email retrieval works:

1. In Claude Desktop: `"Draft a reply to [sender name] saying thank you"`
2. Check your Gmail drafts folder
3. You should see the draft reply

---

## Quick Reference

**Project Details**:
- Project ID: `marine-fusion-482815-b9`
- Client ID: `932357491738-ein80jfvgt7misrt0rbtjuf9opesenh4.apps.googleusercontent.com`

**File Locations**:
- Server: `/Users/taniasantana/Documents/HUB/gmail-mcp-server/gmail_server.py`
- Config: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Logs: `~/Library/Logs/Claude/mcp-server-gmail.log`
- Credentials: `/Users/taniasantana/Documents/HUB/gmail-mcp-server/credentials.json`
- Token (created after auth): `/Users/taniasantana/Documents/HUB/gmail-mcp-server/token.json`

**Useful Commands**:

```bash
# View live logs
tail -f ~/Library/Logs/Claude/mcp-server-gmail.log

# Restart Claude Desktop
pkill -9 "Claude" && sleep 2 && open -a "Claude"

# Check if token exists (after first auth)
ls -la /Users/taniasantana/Documents/HUB/gmail-mcp-server/token.json

# Re-authorize (if needed)
rm /Users/taniasantana/Documents/HUB/gmail-mcp-server/token.json
# Then try "Check my unread emails" again
```

---

## Summary of Changes Made Today

1. **Rewrote server** from FastMCP to standard MCP SDK
   - Fixed initialization timeout issue (60s → <1s)
   - More stable and reliable

2. **Recreated virtual environment**
   - Fixed corrupted package installations
   - Clean install of all dependencies

3. **Fixed file paths**
   - Changed to absolute paths for credentials.json and token.json
   - Ensures files are found regardless of working directory

4. **Server now working**
   - Connects successfully to Claude Desktop
   - Tools properly registered
   - OAuth flow initiates correctly

**Next step tomorrow**: Just follow Steps 1-7 above to complete OAuth setup!

---

Good work today! Get some rest. Tomorrow will be quick - just OAuth configuration and you're done.
