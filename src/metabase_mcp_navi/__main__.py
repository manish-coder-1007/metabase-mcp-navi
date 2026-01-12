#!/usr/bin/env python3
"""
Entry point for running Metabase MCP Server as a module.

Usage:
    uvx metabase-mcp-navi          # Run without installation
    python -m metabase_mcp_navi    # Run as module
"""

from metabase_mcp_navi.server import main

if __name__ == "__main__":
    main()
