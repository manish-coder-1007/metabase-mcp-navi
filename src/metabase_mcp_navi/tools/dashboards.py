"""
Dashboard-related MCP tools.
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError
from metabase_mcp_navi.models import Dashboard

logger = logging.getLogger("metabase-mcp.tools.dashboards")


def register_dashboard_tools(mcp: FastMCP) -> None:
    """Register all dashboard-related tools with the MCP server."""
    
    @mcp.tool()
    def list_dashboards(
        collection_id: Optional[int] = None,
        limit: int = 100
    ) -> str:
        """
        List all dashboards accessible to the current user.
        
        Args:
            collection_id: Optional collection ID to filter by
            limit: Maximum number of dashboards to return (default 100)
        
        Returns:
            Markdown formatted list of dashboards
        """
        try:
            client = get_client()
            
            # Get dashboards
            dashboards = client.get("/api/dashboard")
            
            if not dashboards:
                return "No dashboards found."
            
            # Filter by collection if specified
            if collection_id is not None:
                dashboards = [d for d in dashboards if d.get("collection_id") == collection_id]
            
            # Limit results
            dashboards = dashboards[:limit]
            
            # Format output
            result = [f"### 📊 Dashboards ({len(dashboards)} found)\n"]
            result.append("| ID | Name | Collection | Description |")
            result.append("| --- | --- | --- | --- |")
            
            for d in dashboards:
                name = d.get("name", "Unnamed")[:40]
                desc = (d.get("description") or "")[:30]
                collection = d.get("collection_id", "Root")
                result.append(f"| {d['id']} | {name} | {collection} | {desc} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error listing dashboards: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in list_dashboards")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_dashboard(dashboard_id: int) -> str:
        """
        Get detailed information about a specific dashboard.
        
        Args:
            dashboard_id: The ID of the dashboard
        
        Returns:
            Dashboard details including all cards
        """
        try:
            client = get_client()
            
            data = client.get(f"/api/dashboard/{dashboard_id}")
            dashboard = Dashboard.from_api(data)
            
            # Format output
            result = [f"## 📊 Dashboard: {dashboard.name}"]
            result.append(f"**ID:** {dashboard.id}")
            
            if dashboard.description:
                result.append(f"**Description:** {dashboard.description}")
            
            result.append(f"**Collection ID:** {dashboard.collection_id or 'Root'}")
            result.append(f"**Cards Count:** {len(dashboard.cards)}")
            
            # List parameters if any
            if dashboard.parameters:
                result.append("\n### Parameters")
                for param in dashboard.parameters:
                    result.append(f"- **{param.get('name', 'unnamed')}** ({param.get('type', 'unknown')}): {param.get('slug', '')}")
            
            # List cards
            if dashboard.cards:
                result.append("\n### Cards")
                result.append("| ID | Card ID | Name | Position |")
                result.append("| --- | --- | --- | --- |")
                for card in dashboard.cards:
                    position = f"({card.col}, {card.row})"
                    result.append(f"| {card.id} | {card.card_id} | {card.card_name[:40]} | {position} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting dashboard {dashboard_id}: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_dashboard")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_dashboard_cards(dashboard_id: int) -> str:
        """
        Get all cards (questions) from a specific dashboard.
        
        Args:
            dashboard_id: The ID of the dashboard
        
        Returns:
            List of cards with their details
        """
        try:
            client = get_client()
            
            data = client.get(f"/api/dashboard/{dashboard_id}")
            dashboard = Dashboard.from_api(data)
            
            if not dashboard.cards:
                return f"Dashboard {dashboard_id} ({dashboard.name}) has no cards."
            
            result = [f"### 🃏 Cards in Dashboard: {dashboard.name}\n"]
            result.append(f"**Total Cards:** {len(dashboard.cards)}\n")
            result.append("| Card ID | Name | Size | Position |")
            result.append("| --- | --- | --- | --- |")
            
            for card in dashboard.cards:
                size = f"{card.size_x}x{card.size_y}"
                position = f"row:{card.row}, col:{card.col}"
                result.append(f"| {card.card_id} | {card.card_name[:50]} | {size} | {position} |")
            
            result.append(f"\n**Tip:** Use `execute_card(card_id)` to run any of these cards.")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting dashboard cards: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_dashboard_cards")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def search_dashboards(query: str, limit: int = 20) -> str:
        """
        Search for dashboards by name or description.
        
        Args:
            query: Search term
            limit: Maximum results to return (default 20)
        
        Returns:
            Matching dashboards
        """
        try:
            client = get_client()
            
            # Use Metabase search API
            results = client.get("/api/search", params={
                "q": query,
                "models": "dashboard",
                "limit": limit
            })
            
            items = results.get("data", results) if isinstance(results, dict) else results
            
            if not items:
                return f"No dashboards found matching '{query}'"
            
            result = [f"### 🔍 Search Results for '{query}'\n"]
            result.append("| ID | Name | Collection | Description |")
            result.append("| --- | --- | --- | --- |")
            
            for item in items[:limit]:
                if item.get("model") == "dashboard" or "id" in item:
                    name = item.get("name", "Unnamed")[:40]
                    desc = (item.get("description") or "")[:30]
                    collection = item.get("collection", {}).get("name", "Root") if isinstance(item.get("collection"), dict) else "Root"
                    result.append(f"| {item['id']} | {name} | {collection} | {desc} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error searching dashboards: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in search_dashboards")
            return f"❌ Unexpected error: {str(e)}"
