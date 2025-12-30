# Gmail MCP Server Troubleshooting Guide

## Current Status

**Date**: 2025-12-30
**Issue**: MCP server times out during initialization (60 second timeout)
**Changes Made**:
- Created Python 3.12 virtual environment (`venv/`)
- Downgraded MCP from 1.25.0 → 1.10.0
- Reinstalled Google API packages
- Added `cwd` parameter to Claude Desktop config

## What To Do After Restart

### Step 1: Verify Environment

```bash
# Check virtual environment exists
ls -la venv/

# Check MCP version (should be 1.10.0)
venv/bin/pip list | grep mcp

# Check Python version (should be 3.12.x)
venv/bin/python --version
```

### Step 2: Test Server Standalone

```bash
# Test if FastMCP imports without hanging (should complete in < 3 seconds)
timeout 3 venv/bin/python -c "from mcp.server.fastmcp import FastMCP; print('✅ FastMCP OK')"

# If above works, test full server import (should complete in < 5 seconds)
timeout 5 venv/bin/python -c "from gmail_server import mcp; print('✅ Server imports OK')"

# Test server starts (press Ctrl+C after 3 seconds if it doesn't hang)
venv/bin/python gmail_server.py
```

**Expected**: Server should start without errors and wait for input

**If it hangs**: Skip to "Plan B: Rewrite with Standard SDK"

### Step 3: Restart Claude Desktop

```bash
# Kill all Claude processes
pkill -9 "Claude"

# Wait 2 seconds
sleep 2

# Reopen Claude Desktop
open -a "Claude"
```

### Step 4: Check Logs

```bash
# View latest MCP logs
tail -50 ~/Library/Logs/Claude/mcp-server-gmail.log

# Look for these indicators:
# ✅ GOOD: "Server started and connected successfully"
# ✅ GOOD: "Message from server" with tools listed
# ❌ BAD: "Request timed out"
# ❌ BAD: "Server disconnected"
```

### Step 5: Test in Claude Desktop

1. Open a **new conversation** (important!)
2. Try this prompt: `"Check my unread emails"`
3. Look for:
   - Tool invocation message
   - Browser window for Gmail OAuth (first time)

## If Still Not Working

### Check Current Config

```bash
# Verify config syntax
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Should show:
# {
#   "mcpServers": {
#     "gmail": {
#       "command": "/Users/taniasantana/Documents/HUB/gmail-mcp-server/venv/bin/python",
#       "args": ["/Users/taniasantana/Documents/HUB/gmail-mcp-server/gmail_server.py"],
#       "cwd": "/Users/taniasantana/Documents/HUB/gmail-mcp-server"
#     }
#   }
# }
```

### Common Issues & Fixes

**Issue**: "Server started" but then "Request timed out"
**Cause**: Server hanging during initialization
**Fix**: Proceed to Plan B

**Issue**: "credentials.json not found"
**Fix**:
```bash
ls -la /Users/taniasantana/Documents/HUB/gmail-mcp-server/credentials.json
```

**Issue**: "Module not found"
**Fix**:
```bash
cd /Users/taniasantana/Documents/HUB/gmail-mcp-server
venv/bin/pip install -r requirements.txt
```

## Plan B: Rewrite with Standard MCP SDK

If the server continues to timeout after restart, the issue is with FastMCP initialization hanging. The solution:

1. Rewrite `gmail_server.py` to use the standard MCP SDK instead of FastMCP
2. Standard SDK is more stable and doesn't have the hanging issue
3. Estimated time: 15-20 minutes

### Why This Is Necessary

- FastMCP convenience library has initialization issues
- Standard MCP SDK is lower-level but more reliable
- All functionality will remain the same
- Better for production use

## Success Criteria

✅ Server starts without timing out (< 5 seconds)
✅ Claude Desktop shows gmail server connected
✅ Can call `get_unread_emails` tool
✅ OAuth flow completes successfully
✅ Emails are retrieved

## Useful Commands

```bash
# View live logs
tail -f ~/Library/Logs/Claude/mcp-server-gmail.log

# Check if server process is running
ps aux | grep gmail_server.py

# Test server manually with timeout
timeout 10 venv/bin/python gmail_server.py

# Check credentials exist
ls -la credentials.json token.json

# Reinstall specific MCP version if needed
venv/bin/pip install --force-reinstall mcp==1.10.0
```

## Notes

- Virtual environment MUST be used (system Python 3.9.6 doesn't support MCP)
- MCP 1.25.0 has known hanging issues
- MCP 1.10.0 is more stable but may still have issues with FastMCP
- Standard MCP SDK is the most reliable long-term solution
- The `cwd` parameter is critical for finding credentials.json
