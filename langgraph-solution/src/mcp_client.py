"""MCP Client for interacting with the Energy Processes Database."""

import httpx
from typing import Any, Optional
from src.config import Config


class MCPClient:
    """Client for MCP database operations."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or Config.MCP_BASE_URL
        self.client = httpx.Client(timeout=30.0)
    
    async def execute_select(self, query: str, params: Optional[list] = None) -> dict[str, Any]:
        """Execute a SELECT query on the database."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "execute_select",
                        "arguments": {
                            "query": query,
                            "params": params
                        }
                    },
                    "id": 1
                }
            )
            return response.json()
    
    async def execute_write(self, query: str, params: Optional[list] = None) -> dict[str, Any]:
        """Execute an INSERT, UPDATE, or DELETE query on the database."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "execute_write",
                        "arguments": {
                            "query": query,
                            "params": params
                        }
                    },
                    "id": 1
                }
            )
            return response.json()
    
    async def get_schema(self, schema_name: str = "public", table_name: Optional[str] = None) -> dict[str, Any]:
        """Get the database schema information."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            arguments = {"schema_name": schema_name}
            if table_name:
                arguments["table_name"] = table_name
            
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_schema",
                        "arguments": arguments
                    },
                    "id": 1
                }
            )
            return response.json()


# Singleton instance
mcp_client = MCPClient()
