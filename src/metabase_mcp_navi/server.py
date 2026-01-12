"""
Metabase MCP Server.
Main server module that registers all tools and starts the MCP server.
"""

import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (stdout is used for MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("metabase-mcp")

# Initialize FastMCP server at module level (like trino-mcp-navi)
mcp = FastMCP("metabase")

# Import tools registration functions
from metabase_mcp_navi.tools import (
    register_dashboard_tools,
    register_card_tools,
    register_database_tools,
    register_query_tools,
    register_image_tools,
    register_crud_tools
)

# Import client (but don't create it yet - only when tools are called)
from metabase_mcp_navi.client import get_client
from metabase_mcp_navi.config import get_config

# Register all tools at module level
register_dashboard_tools(mcp)
register_card_tools(mcp)
register_database_tools(mcp)
register_query_tools(mcp)
register_image_tools(mcp)
register_crud_tools(mcp)


# Add connection test tool
@mcp.tool()
def test_connection() -> str:
    """
    Test the connection to Metabase.
    Use this to verify connectivity and authentication.
    
    Returns:
        Connection status and user information
    """
    try:
        client = get_client()
        result = client.test_connection()
        
        if result["success"]:
            return f"""### ✅ Connection Successful

**User:** {result['user']}
**Email:** {result['email']}
**Superuser:** {result['is_superuser']}
**Metabase URL:** {client.config.url}
**Auth Method:** {client.config.auth_method.value}
"""
        else:
            return f"""### ❌ Connection Failed

**Error:** {result['error']}
**Status Code:** {result.get('status_code', 'N/A')}
"""
    except Exception as e:
        return f"❌ Connection test failed: {str(e)}"


@mcp.tool()
def list_collections(parent_id: int = None) -> str:
    """
    List all collections (folders) in Metabase.
    
    Args:
        parent_id: Optional parent collection ID to list children
    
    Returns:
        List of collections
    """
    try:
        client = get_client()
        
        collections = client.get("/api/collection")
        
        if not collections:
            return "No collections found."
        
        # Filter by parent if specified
        if parent_id is not None:
            collections = [c for c in collections if c.get("parent_id") == parent_id]
        
        # Format output
        result = ["### 📁 Collections\n"]
        result.append("| ID | Name | Parent | Items |")
        result.append("| --- | --- | --- | --- |")
        
        for c in collections[:100]:
            name = c.get("name", "Unnamed")[:40]
            parent = c.get("parent_id", "Root")
            if c.get("personal_owner_id"):
                name = f"👤 {name}"
            result.append(f"| {c.get('id', 'N/A')} | {name} | {parent} | - |")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error listing collections: {str(e)}"


@mcp.tool()
def get_collection_items(collection_id: int, item_type: str = "all") -> str:
    """
    Get items (dashboards, cards, collections) in a collection.
    
    Args:
        collection_id: The ID of the collection (use "root" for root collection)
        item_type: Type of items to return: "all", "dashboard", "card", "collection"
    
    Returns:
        Items in the collection
    """
    try:
        client = get_client()
        
        params = {}
        if item_type != "all":
            params["models"] = item_type
        
        items = client.get(f"/api/collection/{collection_id}/items", params=params if params else None)
        
        data = items.get("data", items) if isinstance(items, dict) else items
        
        if not data:
            return f"No items found in collection {collection_id}"
        
        # Format output
        result = [f"### 📁 Collection {collection_id} Items\n"]
        result.append("| Type | ID | Name | Description |")
        result.append("| --- | --- | --- | --- |")
        
        for item in data[:100]:
            model = item.get("model", "unknown")
            icon = {"dashboard": "📊", "card": "🃏", "collection": "📁"}.get(model, "📄")
            name = item.get("name", "Unnamed")[:40]
            desc = (item.get("description") or "")[:30]
            result.append(f"| {icon} {model} | {item.get('id')} | {name} | {desc} |")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error getting collection items: {str(e)}"


def main():
    """Entry point for the MCP server."""
    logger.info("Starting Metabase MCP server with stdio transport")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
