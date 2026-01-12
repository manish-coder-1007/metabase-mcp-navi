"""
Database-related MCP tools.
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError

logger = logging.getLogger("metabase-mcp.tools.databases")


def register_database_tools(mcp: FastMCP) -> None:
    """Register all database-related tools with the MCP server."""
    
    @mcp.tool()
    def list_databases() -> str:
        """
        List all databases connected to Metabase.
        
        Returns:
            Markdown formatted list of databases
        """
        try:
            client = get_client()
            
            databases = client.get("/api/database")
            
            # Handle different response formats
            if isinstance(databases, dict):
                databases = databases.get("data", [])
            
            if not databases:
                return "No databases found."
            
            # Format output
            result = ["### 🗄️ Databases\n"]
            result.append("| ID | Name | Engine | Description |")
            result.append("| --- | --- | --- | --- |")
            
            for db in databases:
                name = db.get("name", "Unnamed")[:30]
                engine = db.get("engine", "unknown")
                desc = (db.get("description") or "")[:40]
                result.append(f"| {db['id']} | {name} | {engine} | {desc} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error listing databases: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in list_databases")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_database(database_id: int) -> str:
        """
        Get detailed information about a specific database.
        
        Args:
            database_id: The ID of the database
        
        Returns:
            Database details
        """
        try:
            client = get_client()
            
            data = client.get(f"/api/database/{database_id}")
            
            # Format output
            result = [f"## 🗄️ Database: {data.get('name', 'Unnamed')}"]
            result.append(f"**ID:** {data['id']}")
            result.append(f"**Engine:** {data.get('engine', 'unknown')}")
            
            if data.get("description"):
                result.append(f"**Description:** {data['description']}")
            
            # Connection details (sanitized)
            details = data.get("details", {})
            if details:
                result.append("\n### Connection Details")
                if details.get("host"):
                    result.append(f"- **Host:** {details['host']}")
                if details.get("port"):
                    result.append(f"- **Port:** {details['port']}")
                if details.get("db") or details.get("dbname"):
                    result.append(f"- **Database:** {details.get('db') or details.get('dbname')}")
            
            # Features
            features = data.get("features", [])
            if features:
                result.append(f"\n**Features:** {', '.join(features[:10])}")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting database {database_id}: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_database")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def list_tables(database_id: int, schema: Optional[str] = None) -> str:
        """
        List all tables in a database.
        
        Args:
            database_id: The ID of the database
            schema: Optional schema name to filter by
        
        Returns:
            List of tables in the database
        """
        try:
            client = get_client()
            
            # Get database metadata including tables
            data = client.get(f"/api/database/{database_id}/metadata")
            
            tables = data.get("tables", [])
            
            if not tables:
                return f"No tables found in database {database_id}"
            
            # Filter by schema if specified
            if schema:
                tables = [t for t in tables if t.get("schema") == schema]
            
            # Get unique schemas for summary
            schemas = set(t.get("schema") for t in data.get("tables", []) if t.get("schema"))
            
            # Format output
            result = [f"### 📋 Tables in Database {database_id}\n"]
            result.append(f"**Total Tables:** {len(tables)}")
            if schemas:
                result.append(f"**Schemas:** {', '.join(sorted(schemas))}")
            result.append("")
            result.append("| ID | Schema | Table Name | Display Name |")
            result.append("| --- | --- | --- | --- |")
            
            # Limit to 100 tables to avoid overwhelming output
            for t in tables[:100]:
                schema_name = t.get("schema", "default")[:20]
                name = t.get("name", "unknown")[:30]
                display = t.get("display_name", name)[:30]
                result.append(f"| {t['id']} | {schema_name} | {name} | {display} |")
            
            if len(tables) > 100:
                result.append(f"\n*... {len(tables) - 100} more tables*")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error listing tables: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in list_tables")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_table_metadata(database_id: int, table_id: int) -> str:
        """
        Get detailed metadata about a specific table including columns.
        
        Args:
            database_id: The ID of the database
            table_id: The ID of the table
        
        Returns:
            Table metadata including columns
        """
        try:
            client = get_client()
            
            # Get table metadata
            data = client.get(f"/api/table/{table_id}/query_metadata")
            
            table_info = data
            
            # Format output
            result = [f"## 📋 Table: {table_info.get('display_name', table_info.get('name', 'Unknown'))}"]
            result.append(f"**ID:** {table_info.get('id')}")
            result.append(f"**Schema:** {table_info.get('schema', 'default')}")
            result.append(f"**Name:** {table_info.get('name')}")
            
            if table_info.get("description"):
                result.append(f"**Description:** {table_info['description']}")
            
            # List columns
            fields = table_info.get("fields", [])
            if fields:
                result.append(f"\n### Columns ({len(fields)})")
                result.append("| ID | Name | Type | Description |")
                result.append("| --- | --- | --- | --- |")
                
                for f in fields:
                    name = f.get("display_name", f.get("name", "unknown"))[:30]
                    base_type = f.get("base_type", "unknown").replace("type/", "")
                    desc = (f.get("description") or "")[:30]
                    result.append(f"| {f.get('id')} | {name} | {base_type} | {desc} |")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting table metadata: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_table_metadata")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def sync_database(database_id: int) -> str:
        """
        Trigger a sync of a database's metadata.
        
        Args:
            database_id: The ID of the database to sync
        
        Returns:
            Sync status
        """
        try:
            client = get_client()
            
            client.post(f"/api/database/{database_id}/sync")
            
            return f"✅ Sync triggered for database {database_id}. This may take a few minutes."
            
        except MetabaseClientError as e:
            return f"❌ Error syncing database: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in sync_database")
            return f"❌ Unexpected error: {str(e)}"
