"""
CRUD tools for Metabase MCP.
Handles creating, updating, and deleting cards, dashboards, and collections.
"""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError


def register_crud_tools(mcp: FastMCP) -> None:
    """Register all CRUD-related tools with the MCP server."""
    
    @mcp.tool()
    def create_collection(
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> str:
        """
        Create a new collection (folder) to organize dashboards and cards.
        
        Args:
            name: Name of the collection
            description: Optional description
            parent_id: Optional parent collection ID (for nested collections)
        
        Returns:
            Created collection details
        """
        try:
            client = get_client()
            
            payload = {
                "name": name,
                "color": "#509EE3"  # Default Metabase blue
            }
            
            if description:
                payload["description"] = description
            if parent_id:
                payload["parent_id"] = parent_id
            
            result = client.post("/api/collection", json_data=payload)
            
            return f"""### ✅ Collection Created

**ID:** {result.get('id')}
**Name:** {result.get('name')}
**Parent:** {result.get('parent_id', 'Root')}
**Location:** {result.get('location', '/')}
"""
        except MetabaseClientError as e:
            return f"❌ Error creating collection: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def create_card(
        name: str,
        database_id: int,
        query: str,
        display: str = "table",
        description: Optional[str] = None,
        collection_id: Optional[int] = None
    ) -> str:
        """
        Create a new card (saved question) with a native SQL query.
        
        Args:
            name: Name of the card/question
            database_id: ID of the database to query
            query: SQL query string
            display: Visualization type: table, line, bar, pie, scalar, row, area, combo, pivot, funnel, map
            description: Optional description
            collection_id: Optional collection ID to save the card in
        
        Returns:
            Created card details
        """
        try:
            client = get_client()
            
            payload = {
                "name": name,
                "dataset_query": {
                    "type": "native",
                    "native": {
                        "query": query
                    },
                    "database": database_id
                },
                "display": display,
                "visualization_settings": {}
            }
            
            if description:
                payload["description"] = description
            if collection_id:
                payload["collection_id"] = collection_id
            
            result = client.post("/api/card", json_data=payload)
            
            card_id = result.get('id')
            metabase_url = client.config.url
            
            return f"""### ✅ Card Created

**ID:** {card_id}
**Name:** {result.get('name')}
**Display:** {result.get('display')}
**Database ID:** {database_id}
**Collection ID:** {result.get('collection_id', 'Root')}

**URL:** {metabase_url}/question/{card_id}

**Query:**
```sql
{query}
```
"""
        except MetabaseClientError as e:
            if e.response:
                return f"❌ Error creating card: {e.response}"
            return f"❌ Error creating card: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def create_dashboard(
        name: str,
        description: Optional[str] = None,
        collection_id: Optional[int] = None
    ) -> str:
        """
        Create a new empty dashboard.
        
        Args:
            name: Name of the dashboard
            description: Optional description
            collection_id: Optional collection ID to save the dashboard in
        
        Returns:
            Created dashboard details
        """
        try:
            client = get_client()
            
            payload = {
                "name": name
            }
            
            if description:
                payload["description"] = description
            if collection_id:
                payload["collection_id"] = collection_id
            
            result = client.post("/api/dashboard", json_data=payload)
            
            dashboard_id = result.get('id')
            metabase_url = client.config.url
            
            return f"""### ✅ Dashboard Created

**ID:** {dashboard_id}
**Name:** {result.get('name')}
**Collection ID:** {result.get('collection_id', 'Root')}

**URL:** {metabase_url}/dashboard/{dashboard_id}

*Use `add_card_to_dashboard` to add cards to this dashboard.*
"""
        except MetabaseClientError as e:
            return f"❌ Error creating dashboard: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def add_card_to_dashboard(
        dashboard_id: int,
        card_id: int,
        row: int = 0,
        col: int = 0,
        size_x: int = 8,
        size_y: int = 6
    ) -> str:
        """
        Add an existing card to a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            card_id: ID of the card to add
            row: Row position (default: 0)
            col: Column position (default: 0, max: 17)
            size_x: Width in grid units (default: 8, max: 18)
            size_y: Height in grid units (default: 6)
        
        Returns:
            Success message with dashcard details
        """
        try:
            client = get_client()
            
            # Get card info for context
            card = client.get(f"/api/card/{card_id}")
            card_name = card.get("name", "Unknown")
            
            # Get existing dashboard to get current dashcards
            dashboard = client.get(f"/api/dashboard/{dashboard_id}")
            existing_dashcards = dashboard.get("dashcards", [])
            
            # Create new dashcard entry (id=-1 means new)
            new_dashcard = {
                "id": -1,
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": size_x,
                "size_y": size_y
            }
            
            # Add to existing dashcards
            updated_dashcards = existing_dashcards + [new_dashcard]
            
            # Update dashboard with new dashcards array
            result = client.put(f"/api/dashboard/{dashboard_id}", json_data={"dashcards": updated_dashcards})
            
            # Find the newly added dashcard
            new_dashcards = result.get("dashcards", [])
            added_dashcard = None
            for dc in new_dashcards:
                if dc.get("card_id") == card_id:
                    added_dashcard = dc
                    break
            
            dashcard_id = added_dashcard.get("id") if added_dashcard else "Unknown"
            
            return f"""### ✅ Card Added to Dashboard

**Dashboard ID:** {dashboard_id}
**Card ID:** {card_id}
**Card Name:** {card_name}
**Position:** Row {row}, Col {col}
**Size:** {size_x} x {size_y}
**DashCard ID:** {dashcard_id}
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Dashboard {dashboard_id} or Card {card_id} not found"
            return f"❌ Error adding card to dashboard: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def remove_card_from_dashboard(
        dashboard_id: int,
        dashcard_id: int
    ) -> str:
        """
        Remove a card from a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            dashcard_id: ID of the dashcard (not the card ID - get this from dashboard info)
        
        Returns:
            Success message
        """
        try:
            client = get_client()
            
            # Get existing dashboard
            dashboard = client.get(f"/api/dashboard/{dashboard_id}")
            existing_dashcards = dashboard.get("dashcards", [])
            
            # Filter out the dashcard to remove
            updated_dashcards = [dc for dc in existing_dashcards if dc.get("id") != dashcard_id]
            
            if len(updated_dashcards) == len(existing_dashcards):
                return f"❌ DashCard {dashcard_id} not found in dashboard {dashboard_id}"
            
            # Update dashboard with filtered dashcards
            client.put(f"/api/dashboard/{dashboard_id}", json_data={"dashcards": updated_dashcards})
            
            return f"""### ✅ Card Removed from Dashboard

**Dashboard ID:** {dashboard_id}
**DashCard ID:** {dashcard_id}

*The card still exists but is no longer on this dashboard.*
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Dashboard {dashboard_id} not found"
            return f"❌ Error removing card: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def update_card(
        card_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        query: Optional[str] = None,
        display: Optional[str] = None,
        collection_id: Optional[int] = None
    ) -> str:
        """
        Update an existing card's properties.
        
        Args:
            card_id: ID of the card to update
            name: New name (optional)
            description: New description (optional)
            query: New SQL query (optional)
            display: New visualization type (optional)
            collection_id: Move to different collection (optional)
        
        Returns:
            Updated card details
        """
        try:
            client = get_client()
            
            # Get current card data
            current = client.get(f"/api/card/{card_id}")
            
            payload = {}
            
            if name:
                payload["name"] = name
            if description is not None:
                payload["description"] = description
            if display:
                payload["display"] = display
            if collection_id:
                payload["collection_id"] = collection_id
            if query:
                # Update the query while preserving other dataset_query settings
                dataset_query = current.get("dataset_query", {})
                if dataset_query.get("type") == "native":
                    dataset_query["native"]["query"] = query
                    payload["dataset_query"] = dataset_query
                else:
                    return "❌ Can only update query for native SQL cards"
            
            if not payload:
                return "⚠️ No updates specified"
            
            result = client.put(f"/api/card/{card_id}", json_data=payload)
            
            changes = ", ".join(payload.keys())
            
            return f"""### ✅ Card Updated

**ID:** {card_id}
**Name:** {result.get('name')}
**Display:** {result.get('display')}
**Collection ID:** {result.get('collection_id', 'Root')}

**Updated Fields:** {changes}
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Card {card_id} not found"
            return f"❌ Error updating card: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def delete_card(card_id: int) -> str:
        """
        Delete a card (saved question).
        WARNING: This action cannot be undone!
        
        Args:
            card_id: ID of the card to delete
        
        Returns:
            Confirmation message
        """
        try:
            client = get_client()
            
            # Get card info before deleting
            card = client.get(f"/api/card/{card_id}")
            card_name = card.get("name", "Unknown")
            
            client.delete(f"/api/card/{card_id}")
            
            return f"""### ✅ Card Deleted

**ID:** {card_id}
**Name:** {card_name}

⚠️ This action cannot be undone.
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Card {card_id} not found"
            return f"❌ Error deleting card: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def delete_dashboard(dashboard_id: int) -> str:
        """
        Delete a dashboard.
        WARNING: This action cannot be undone!
        
        Args:
            dashboard_id: ID of the dashboard to delete
        
        Returns:
            Confirmation message
        """
        try:
            client = get_client()
            
            # Get dashboard info before deleting
            dashboard = client.get(f"/api/dashboard/{dashboard_id}")
            dashboard_name = dashboard.get("name", "Unknown")
            
            client.delete(f"/api/dashboard/{dashboard_id}")
            
            return f"""### ✅ Dashboard Deleted

**ID:** {dashboard_id}
**Name:** {dashboard_name}

⚠️ This action cannot be undone.
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Dashboard {dashboard_id} not found"
            return f"❌ Error deleting dashboard: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def delete_collection(collection_id: int) -> str:
        """
        Delete a collection (folder).
        WARNING: This may affect items inside the collection!
        
        Args:
            collection_id: ID of the collection to delete
        
        Returns:
            Confirmation message
        """
        try:
            client = get_client()
            
            # Get collection info before deleting
            collection = client.get(f"/api/collection/{collection_id}")
            collection_name = collection.get("name", "Unknown")
            
            client.delete(f"/api/collection/{collection_id}")
            
            return f"""### ✅ Collection Deleted

**ID:** {collection_id}
**Name:** {collection_name}

⚠️ Items in this collection may have been moved or affected.
"""
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Collection {collection_id} not found"
            return f"❌ Error deleting collection: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
