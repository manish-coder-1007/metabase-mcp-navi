# Metabase MCP Server

[![PyPI version](https://badge.fury.io/py/metabase-mcp-navi.svg)](https://badge.fury.io/py/metabase-mcp-navi)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for Metabase - gives AI assistants direct access to dashboards, cards, and query execution.

## Features

- **Three Authentication Methods**: API Key, Session ID, or Username/Password
- **Dashboard Tools**: List, search, get details, get cards from dashboards
- **Card Tools**: List, search, get details, execute saved questions
- **Database Tools**: List databases, tables, get metadata, sync
- **Query Tools**: Execute SQL, test queries, get suggestions, explain queries
- **Image Export**: Export cards and dashboards as PNG images
- **CRUD Operations**: Create, update, delete cards, dashboards, and collections

## Quick Start

### Installation

```bash
# Install via pip
pip install metabase-mcp-navi

# Or via uvx (recommended for MCP)
uvx metabase-mcp-navi
```

### Configuration

Set environment variables:

```bash
# Required
export METABASE_URL=https://your-metabase-instance.com

# Authentication (choose one):
export METABASE_API_KEY=your_api_key
# OR
export METABASE_SESSION_ID=your_session_id
# OR
export METABASE_USER_EMAIL=your_email
export METABASE_PASSWORD=your_password

# Optional
export METABASE_VERIFY_SSL=false  # Disable SSL verification
export METABASE_TIMEOUT=60        # Request timeout in seconds
```

### Cursor MCP Configuration

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uvx",
      "args": ["metabase-mcp-navi"],
      "env": {
        "METABASE_URL": "https://your-metabase-instance.com",
        "METABASE_SESSION_ID": "your_session_id",
        "METABASE_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uvx",
      "args": ["metabase-mcp-navi"],
      "env": {
        "METABASE_URL": "https://your-metabase-instance.com",
        "METABASE_SESSION_ID": "your_session_id"
      }
    }
  }
}
```

## Available Tools

### Dashboard Tools
| Tool | Description |
|------|-------------|
| `list_dashboards` | List all accessible dashboards |
| `get_dashboard` | Get dashboard details |
| `get_dashboard_cards` | Get all cards from a dashboard |
| `search_dashboards` | Search dashboards by name |

### Card Tools
| Tool | Description |
|------|-------------|
| `list_cards` | List saved questions |
| `get_card` | Get card details and SQL query |
| `execute_card` | Run a saved question |
| `search_cards` | Search cards by name |

### Database Tools
| Tool | Description |
|------|-------------|
| `list_databases` | List connected databases |
| `get_database` | Get database details |
| `list_tables` | List tables in a database |
| `get_table_metadata` | Get table columns and types |
| `sync_database` | Trigger metadata sync |

### Query Tools
| Tool | Description |
|------|-------------|
| `execute_query` | Execute native SQL |
| `test_query` | Test query with auto LIMIT |
| `get_query_suggestions` | Get suggested queries for a table |
| `explain_query` | Get query execution plan |

### Image Tools
| Tool | Description |
|------|-------------|
| `get_card_image` | Get card as base64 PNG |
| `download_card_image` | Save card image to disk |
| `get_dashboard_cards_as_images` | Check exportable cards |
| `download_all_dashboard_cards` | Download all dashboard images |

### CRUD Tools
| Tool | Description |
|------|-------------|
| `create_collection` | Create a new collection |
| `create_card` | Create a new card with SQL |
| `create_dashboard` | Create a new dashboard |
| `add_card_to_dashboard` | Add card to dashboard |
| `update_card` | Update card properties |
| `delete_card` | Delete a card |
| `delete_dashboard` | Delete a dashboard |

### Other Tools
| Tool | Description |
|------|-------------|
| `test_connection` | Test Metabase connectivity |
| `list_collections` | List folders/collections |
| `get_collection_items` | Browse collection contents |

## Usage Examples

After configuring, you can ask your AI assistant:

- "List all dashboards in Metabase"
- "Get dashboard 3301 details"
- "Execute card 12345"
- "Run this SQL on database 104: SELECT * FROM users LIMIT 10"
- "Search for dashboards about 'payments'"
- "Create a new card with this query..."
- "Download all images from dashboard 42"

## Getting Session ID

1. Open Metabase in your browser and log in
2. Open Developer Tools (F12)
3. Go to Application → Cookies
4. Copy the value of `metabase.SESSION`

## Project Structure

```
metabase-mcp-navi/
├── src/
│   └── metabase_mcp_navi/
│       ├── __init__.py       # Package initialization
│       ├── __main__.py       # Module entry point
│       ├── config.py         # Configuration management
│       ├── client.py         # Metabase API client
│       ├── models.py         # Data models
│       ├── server.py         # MCP server setup
│       └── tools/
│           ├── __init__.py   # Tools package
│           ├── dashboards.py # Dashboard tools
│           ├── cards.py      # Card/question tools
│           ├── databases.py  # Database tools
│           ├── queries.py    # Query execution tools
│           ├── images.py     # Image export tools
│           └── crud.py       # CRUD operations
├── pyproject.toml            # Package configuration
├── README.md
└── LICENSE
```

## Development

```bash
# Clone the repository
git clone https://github.com/manish-coder-1007/metabase-mcp-navi.git
cd metabase-mcp-navi

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Manish Balot

## Related Projects

- [trino-mcp-navi](https://github.com/manish-coder-1007/trino-mcp-navi) - MCP server for Trino databases
