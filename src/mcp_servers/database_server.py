"""MCP server exposing the articles database as tools.

Run standalone: ``python -m src.mcp_servers.database_server``
"""

from __future__ import annotations

import asyncio
import json

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.storage.db_manager import DatabaseManager

server = Server("articles-db")
db = DatabaseManager()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_articles",
            description="Query stored articles, optionally filtered by source.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Filter by source (optional)."},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        types.Tool(
            name="search_articles",
            description="Keyword-search articles by title/summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_sources",
            description="List distinct article sources currently stored.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "query_articles":
        articles = await db.query_articles(
            source=arguments.get("source"), limit=arguments.get("limit", 50)
        )
        payload = {"total": len(articles), "articles": articles}
    elif name == "search_articles":
        articles = await db.search_articles(arguments["query"], limit=arguments.get("limit", 20))
        payload = {"total": len(articles), "articles": articles}
    elif name == "get_sources":
        payload = {"sources": await db.get_sources()}
    else:
        payload = {"error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(payload))]


async def main() -> None:
    await db.initialize()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
