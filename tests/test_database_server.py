"""Tests for the database MCP server's tool handlers (no subprocess/transport)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.mcp_servers import database_server


@pytest.mark.asyncio
async def test_list_tools_declares_expected_tools() -> None:
    tools = await database_server.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"query_articles", "search_articles", "get_sources"}


@pytest.mark.asyncio
async def test_call_tool_query_articles() -> None:
    with patch.object(
        database_server.db, "query_articles", AsyncMock(return_value=[{"title": "A"}])
    ):
        result = await database_server.call_tool("query_articles", {"limit": 10})

    payload = json.loads(result[0].text)
    assert payload["total"] == 1


@pytest.mark.asyncio
async def test_call_tool_search_articles() -> None:
    with patch.object(database_server.db, "search_articles", AsyncMock(return_value=[])):
        result = await database_server.call_tool("search_articles", {"query": "ai"})

    payload = json.loads(result[0].text)
    assert payload["total"] == 0


@pytest.mark.asyncio
async def test_call_tool_get_sources() -> None:
    with patch.object(database_server.db, "get_sources", AsyncMock(return_value=["rss"])):
        result = await database_server.call_tool("get_sources", {})

    payload = json.loads(result[0].text)
    assert payload["sources"] == ["rss"]


@pytest.mark.asyncio
async def test_call_tool_unknown_tool_returns_error_payload() -> None:
    result = await database_server.call_tool("delete_everything", {})
    payload = json.loads(result[0].text)
    assert "error" in payload
