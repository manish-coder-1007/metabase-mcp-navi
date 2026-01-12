# Setting up Metabase MCP for Cursor

This guide will help you configure the Metabase MCP server for use with Cursor IDE.

## Prerequisites

- Python 3.10 or higher
- Cursor IDE installed
- Access to a Metabase instance

## Installation

### Option 1: Using uvx (Recommended)

No installation required! uvx will download and run the package automatically.

### Option 2: Using pip

```bash
pip install metabase-mcp-navi
```

## Configuration

### Step 1: Get Metabase Credentials

You need one of the following authentication methods:

#### Option A: Session ID (Easiest)
1. Log into Metabase in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies
4. Copy the value of `metabase.SESSION`

#### Option B: API Key
1. Go to Metabase Admin → Settings → API Keys
2. Create a new API key
3. Copy the key value

#### Option C: Username/Password
Use your Metabase login credentials.

### Step 2: Configure Cursor

1. Open or create `~/.cursor/mcp.json`

2. Add the Metabase server configuration:

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uvx",
      "args": ["metabase-mcp-navi"],
      "env": {
        "METABASE_URL": "https://your-metabase-instance.com",
        "METABASE_SESSION_ID": "your_session_id_here",
        "METABASE_VERIFY_SSL": "false",
        "METABASE_TIMEOUT": "60"
      }
    }
  }
}
```

Or with username/password:

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uvx",
      "args": ["metabase-mcp-navi"],
      "env": {
        "METABASE_URL": "https://your-metabase-instance.com",
        "METABASE_USER_EMAIL": "your@email.com",
        "METABASE_PASSWORD": "your_password",
        "METABASE_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Step 3: Restart Cursor

After saving the configuration, restart Cursor IDE to load the MCP server.

## Verification

After restarting, try asking the AI assistant:

- "List all databases in Metabase"
- "Test the Metabase connection"

If configured correctly, you should see your Metabase data.

## Troubleshooting

### "Connection Failed" Error

1. Verify your `METABASE_URL` is correct
2. Check if your session ID is valid (they expire!)
3. Try setting `METABASE_VERIFY_SSL=false` if using self-signed certificates

### "Authentication Failed" Error

1. For session ID: Get a fresh session ID from browser cookies
2. For API key: Verify the key hasn't been revoked
3. For username/password: Check credentials are correct

### Server Not Loading

1. Check Cursor's MCP logs for errors
2. Verify Python 3.10+ is installed
3. Try running `uvx metabase-mcp-navi` manually to see errors

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `METABASE_URL` | Yes | Your Metabase instance URL |
| `METABASE_API_KEY` | One of | API key authentication |
| `METABASE_SESSION_ID` | these | Session ID authentication |
| `METABASE_USER_EMAIL` | three | Username for auth |
| `METABASE_PASSWORD` | | Password for auth |
| `METABASE_VERIFY_SSL` | No | Set to "false" to skip SSL verification |
| `METABASE_TIMEOUT` | No | Request timeout in seconds (default: 30) |
