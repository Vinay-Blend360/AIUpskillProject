"""Client-side wrapper for calling the articles-database MCP server."""

from __future__ import annotations

import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PARAMS = StdioServerParameters(
    command="python", args=["-m", "src.mcp_servers.database_server"]
)


class SearchSkill:
    """Looks up previously-stored articles via the database MCP server."""

    def __init__(self, server_params: StdioServerParameters = SERVER_PARAMS) -> None:
        self.server_params = server_params

    async def search(self, query: str, limit: int = 20) -> dict:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "search_articles", {"query": query, "limit": limit}
                    )
                    payload = json.loads(result.content[0].text)
                    return {"success": True, "query": query, **payload}
        except Exception as e:  # noqa: BLE001 - surface any MCP/transport failure to the caller
            return {"success": False, "query": query, "error": str(e)}
