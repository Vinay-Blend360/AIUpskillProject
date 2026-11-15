"""Tests for SearchSkill, with the MCP transport mocked out."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.skills.search_skill import SearchSkill


def _mock_call_tool_result(payload: dict) -> MagicMock:
    content = MagicMock()
    content.text = json.dumps(payload)
    result = MagicMock()
    result.content = [content]
    return result


@pytest.mark.asyncio
async def test_search_returns_parsed_results() -> None:
    session = MagicMock()
    session.initialize = AsyncMock()
    session.call_tool = AsyncMock(
        return_value=_mock_call_tool_result({"total": 1, "articles": [{"title": "A"}]})
    )

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)

    stdio_cm = MagicMock()
    stdio_cm.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
    stdio_cm.__aexit__ = AsyncMock(return_value=False)

    skill = SearchSkill()
    with (
        patch("src.skills.search_skill.stdio_client", return_value=stdio_cm),
        patch("src.skills.search_skill.ClientSession", return_value=session_cm),
    ):
        result = await skill.search("transformers")

    assert result["success"] is True
    assert result["total"] == 1
    session.call_tool.assert_called_once_with(
        "search_articles", {"query": "transformers", "limit": 20}
    )


@pytest.mark.asyncio
async def test_search_reports_failure_on_transport_error() -> None:
    skill = SearchSkill()
    with patch("src.skills.search_skill.stdio_client", side_effect=RuntimeError("no server")):
        result = await skill.search("transformers")

    assert result["success"] is False
    assert "no server" in result["error"]
