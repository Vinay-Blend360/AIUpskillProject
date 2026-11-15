"""Tests for EnhancedFilterAgent's tool-calling relevance judgment."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.enhanced_filter_agent import EnhancedFilterAgent
from src.storage.markdown_sections import write_sections


@pytest.mark.asyncio
async def test_judge_relevance_uses_tool_loop_result(tmp_path: Path) -> None:
    agent = EnhancedFilterAgent(relevance_threshold=6)
    judgment = json.dumps(
        {
            "relevant": True,
            "relevance_score": 8,
            "reasoning": "Major model release.",
            "key_topics": ["LLMs"],
            "priority": 25.0,
        }
    )

    with patch.object(agent, "_call_llm_with_tools", AsyncMock(return_value=judgment)):
        result = await agent._judge_relevance({"title": "GPT-5", "body": "...", "score": 50})

    assert result["relevant"] is True
    assert result["priority"] == 25.0


@pytest.mark.asyncio
async def test_full_execute_with_tools(tmp_path: Path) -> None:
    agent = EnhancedFilterAgent(relevance_threshold=6)
    input_path = write_sections(
        tmp_path / "in.md", [{"title": "GPT-5", "url": "https://a.com", "body": "...", "score": 10}]
    )
    judgment = json.dumps(
        {
            "relevant": True,
            "relevance_score": 9,
            "reasoning": "Relevant.",
            "key_topics": [],
            "priority": 20.0,
        }
    )

    with patch.object(agent, "_call_llm_with_tools", AsyncMock(return_value=judgment)):
        result = await agent.execute(str(input_path), str(tmp_path / "out.md"))

    assert result["total_output"] == 1
