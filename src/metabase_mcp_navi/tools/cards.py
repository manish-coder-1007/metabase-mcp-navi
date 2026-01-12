"""
Card (saved question) related MCP tools.
"""

import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError
from metabase_mcp_navi.models import QueryResult

logger = logging.getLogger("metabase-mcp.tools.cards")


def register_card_tools(mcp: FastMCP) -> None:
    """Register all card-related tools with the MCP server."""
    
    @mcp.tool()
    def list_cards(
        collection_id: Optional[int] = None,
        database_id: Optional[int] = None,
        limit: int = 100
    ) -> str:
        """
        List saved questions (cards) accessible to the current user.
        
        Args:
            collection_id: Optional collection ID to filter by
            database_id: Optional database ID to filter by
            limit: Maximum number of cards to return (default 100)
        
        Returns:
            Markdown formatted list of cards
        """
        try:
            client = get_client()
            
            # Get cards
            params = {}
            if collection_id is not None:
                params["collection"] = collection_id
            
            cards = client.get("/api/card", params=params if params else None)
            
            if not cards:
                return "No cards (saved questions) found."
            
            # Filter by database if specified
            if database_id is not None:
                cards = [c for c in cards if c.get("database_id") == database_id]
            
            # Limit results
            cards = cards[:limit]
            
            # Format output
            result = [f"### 🃏 Cards ({len(cards)} found)\n"]
            result.append("| ID | Name | Type | Database | Collection |")
            result.append("| --- | --- | --- | --- | --- |")
            
            for c in cards:
                name = c.get("name", "Unnamed")[:35]
                query_type = c.get("query_type", "unknown")
                db_id = c.get("database_id", "N/A")
                collection = c.get("collection_id", "Root")
                result.append(f"| {c['id']} | {name} | {query_type} | {db_id} | {collection} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error listing cards: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in list_cards")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_card(card_id: int) -> str:
        """
        Get detailed information about a specific card (saved question).
        
        Args:
            card_id: The ID of the card
        
        Returns:
            Card details including query information
        """
        try:
            client = get_client()
            
            data = client.get(f"/api/card/{card_id}")
            
            # Format output
            result = [f"## 🃏 Card: {data.get('name', 'Unnamed')}"]
            result.append(f"**ID:** {data['id']}")
            
            if data.get("description"):
                result.append(f"**Description:** {data['description']}")
            
            result.append(f"**Type:** {data.get('query_type', 'unknown')}")
            result.append(f"**Display:** {data.get('display', 'table')}")
            result.append(f"**Database ID:** {data.get('database_id', 'N/A')}")
            result.append(f"**Collection ID:** {data.get('collection_id', 'Root')}")
            
            # Show query based on type
            dataset_query = data.get("dataset_query", {})
            
            if data.get("query_type") == "native":
                native_query = dataset_query.get("native", {})
                query_text = native_query.get("query", "")
                if query_text:
                    result.append("\n### SQL Query")
                    result.append(f"```sql\n{query_text}\n```")
            else:
                # Query Builder card - show the JSON structure
                import json
                query_structure = dataset_query.get("query", {})
                if query_structure:
                    result.append("\n### Query Builder JSON")
                    result.append(f"```json\n{json.dumps(query_structure, indent=2)}\n```")
            
            # Show parameters/template tags
            template_tags = data.get("dataset_query", {}).get("native", {}).get("template-tags", {})
            if template_tags:
                result.append("\n### Parameters")
                for name, tag in template_tags.items():
                    tag_type = tag.get("type", "unknown")
                    display_name = tag.get("display-name", name)
                    result.append(f"- **{display_name}** (`{name}`): {tag_type}")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting card {card_id}: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_card")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def execute_card(
        card_id: int,
        parameters: Optional[str] = None,
        max_rows: int = 100
    ) -> str:
        """
        Execute a saved question (card) and return results.
        
        Args:
            card_id: The ID of the card to execute
            parameters: Optional JSON string of parameters (e.g., '{"param1": "value1"}')
            max_rows: Maximum rows to return (default 100)
        
        Returns:
            Query results in markdown table format
        """
        try:
            client = get_client()
            
            # Build request body
            body: Dict[str, Any] = {}
            
            # Parse parameters if provided
            if parameters:
                import json
                try:
                    params = json.loads(parameters)
                    if params:
                        body["parameters"] = [
                            {"type": "category", "target": ["variable", ["template-tag", k]], "value": v}
                            for k, v in params.items()
                        ]
                except json.JSONDecodeError:
                    return f"❌ Invalid parameters JSON: {parameters}"
            
            # Execute the card
            data = client.post(f"/api/card/{card_id}/query", json_data=body if body else None)
            
            # Parse result
            query_result = QueryResult.from_api(data)
            
            # Format output
            result = [f"### ✅ Card {card_id} Results\n"]
            result.append(f"**Rows:** {query_result.row_count}")
            if query_result.running_time:
                result.append(f"**Execution Time:** {query_result.running_time}ms")
            result.append("")
            result.append(query_result.to_markdown_table(max_rows=max_rows))
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error executing card {card_id}: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in execute_card")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def search_cards(query: str, limit: int = 20) -> str:
        """
        Search for cards (saved questions) by name or description.
        
        Args:
            query: Search term
            limit: Maximum results to return (default 20)
        
        Returns:
            Matching cards
        """
        try:
            client = get_client()
            
            # Use Metabase search API
            results = client.get("/api/search", params={
                "q": query,
                "models": "card",
                "limit": limit
            })
            
            items = results.get("data", results) if isinstance(results, dict) else results
            
            if not items:
                return f"No cards found matching '{query}'"
            
            result = [f"### 🔍 Search Results for '{query}'\n"]
            result.append("| ID | Name | Type | Database |")
            result.append("| --- | --- | --- | --- |")
            
            for item in items[:limit]:
                if item.get("model") == "card" or "id" in item:
                    name = item.get("name", "Unnamed")[:40]
                    query_type = item.get("query_type", "unknown")
                    db_id = item.get("database_id", "N/A")
                    result.append(f"| {item['id']} | {name} | {query_type} | {db_id} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error searching cards: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in search_cards")
            return f"❌ Unexpected error: {str(e)}"
