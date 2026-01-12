"""
Query execution MCP tools.
"""

import logging
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError
from metabase_mcp_navi.models import QueryResult

logger = logging.getLogger("metabase-mcp.tools.queries")


def register_query_tools(mcp: FastMCP) -> None:
    """Register all query-related tools with the MCP server."""
    
    @mcp.tool()
    def execute_query(
        database_id: int,
        query: str,
        max_rows: int = 100
    ) -> str:
        """
        Execute a native SQL query against a database.
        
        Args:
            database_id: The ID of the database to query
            query: SQL query to execute
            max_rows: Maximum rows to return (default 100)
        
        Returns:
            Query results in markdown table format
        """
        try:
            client = get_client()
            
            # Build the query payload
            payload = {
                "database": database_id,
                "type": "native",
                "native": {
                    "query": query
                }
            }
            
            # Execute via dataset endpoint
            data = client.post("/api/dataset", json_data=payload)
            
            # Check for errors in response
            if data.get("error"):
                return f"❌ Query error: {data['error']}"
            
            # Parse result
            query_result = QueryResult.from_api(data)
            
            # Format output
            result = ["### ✅ Query Results\n"]
            result.append(f"**Database:** {database_id}")
            result.append(f"**Rows:** {query_result.row_count}")
            if query_result.running_time:
                result.append(f"**Execution Time:** {query_result.running_time}ms")
            result.append("")
            result.append(query_result.to_markdown_table(max_rows=max_rows))
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error executing query: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in execute_query")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def test_query(
        database_id: int,
        query: str,
        limit: int = 10
    ) -> str:
        """
        Test a SQL query with automatic LIMIT (for exploration).
        Automatically adds LIMIT to prevent large result sets.
        
        Args:
            database_id: The ID of the database to query
            query: SQL query to test
            limit: Maximum rows to return (default 10)
        
        Returns:
            Query results preview
        """
        try:
            # Add LIMIT if not present
            query_upper = query.upper().strip()
            if "LIMIT" not in query_upper:
                # Remove trailing semicolon if present
                query = query.rstrip(";").strip()
                query = f"{query} LIMIT {limit}"
            
            # Use execute_query
            return execute_query(database_id=database_id, query=query, max_rows=limit)
            
        except Exception as e:
            logger.exception("Unexpected error in test_query")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_query_suggestions(database_id: int, table_name: str) -> str:
        """
        Get AI-suggested queries for a table based on its structure.
        
        Args:
            database_id: The ID of the database
            table_name: Name of the table
        
        Returns:
            Suggested SQL queries
        """
        try:
            client = get_client()
            
            # Get database metadata to find the table
            data = client.get(f"/api/database/{database_id}/metadata")
            tables = data.get("tables", [])
            
            # Find the table
            target_table = None
            for t in tables:
                if t.get("name", "").lower() == table_name.lower():
                    target_table = t
                    break
            
            if not target_table:
                return f"Table '{table_name}' not found in database {database_id}"
            
            # Get table fields
            fields = target_table.get("fields", [])
            if not fields:
                # Try to get from table endpoint
                table_data = client.get(f"/api/table/{target_table['id']}/query_metadata")
                fields = table_data.get("fields", [])
            
            schema = target_table.get("schema", "")
            full_table = f"{schema}.{table_name}" if schema else table_name
            
            # Generate suggestions
            result = [f"### 💡 Query Suggestions for `{full_table}`\n"]
            
            # Basic select
            field_names = [f.get("name", "") for f in fields[:10]]
            select_fields = ", ".join(field_names) if field_names else "*"
            result.append("**1. Sample Data:**")
            result.append(f"```sql\nSELECT {select_fields}\nFROM {full_table}\nLIMIT 10\n```\n")
            
            # Row count
            result.append("**2. Row Count:**")
            result.append(f"```sql\nSELECT COUNT(*) as total_rows\nFROM {full_table}\n```\n")
            
            # Find date/time fields for time-based queries
            date_fields = [f for f in fields if "date" in f.get("base_type", "").lower() or "time" in f.get("base_type", "").lower()]
            if date_fields:
                date_field = date_fields[0].get("name")
                result.append("**3. Recent Records:**")
                result.append(f"```sql\nSELECT *\nFROM {full_table}\nORDER BY {date_field} DESC\nLIMIT 20\n```\n")
            
            # Find numeric fields for aggregation
            numeric_fields = [f for f in fields if "number" in f.get("base_type", "").lower() or "integer" in f.get("base_type", "").lower() or "float" in f.get("base_type", "").lower()]
            if numeric_fields:
                num_field = numeric_fields[0].get("name")
                result.append("**4. Numeric Summary:**")
                result.append(f"```sql\nSELECT \n  COUNT(*) as count,\n  SUM({num_field}) as total,\n  AVG({num_field}) as average,\n  MIN({num_field}) as min_val,\n  MAX({num_field}) as max_val\nFROM {full_table}\n```\n")
            
            # Find potential grouping fields (text/categorical)
            text_fields = [f for f in fields if "text" in f.get("base_type", "").lower() or "string" in f.get("base_type", "").lower()][:3]
            if text_fields:
                group_field = text_fields[0].get("name")
                result.append("**5. Group By Distribution:**")
                result.append(f"```sql\nSELECT {group_field}, COUNT(*) as count\nFROM {full_table}\nGROUP BY {group_field}\nORDER BY count DESC\nLIMIT 20\n```\n")
            
            return "\n".join(result)
            
        except MetabaseClientError as e:
            return f"❌ Error getting suggestions: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in get_query_suggestions")
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def explain_query(database_id: int, query: str) -> str:
        """
        Get the query execution plan (EXPLAIN) for a SQL query.
        
        Args:
            database_id: The ID of the database
            query: SQL query to explain
        
        Returns:
            Query execution plan
        """
        try:
            # Prepend EXPLAIN to the query
            explain_query = f"EXPLAIN {query}"
            
            return execute_query(database_id=database_id, query=explain_query, max_rows=100)
            
        except Exception as e:
            logger.exception("Unexpected error in explain_query")
            return f"❌ Unexpected error: {str(e)}"
