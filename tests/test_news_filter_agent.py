"""Tests for NewsFilterAgent, with the LLM call mocked out."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.news_filter_agent import NewsFilterAgent
from src.storage.markdown_sections import load_sections, write_sections

RELEVANT_JUDGMENT = json.dumps(
    {
        "relevant": True,
        "relevance_score": 9,
        "reasoning": "Discusses a major LLM release.",
        "key_topics": ["LLMs", "GPT"],
    }
)
NOT_RELEVANT_JUDGMENT = json.dumps(
    {
        "relevant": False,
        "relevance_score": 1,
        "reasoning": "Unrelated to AI.",
        "key_topics": [],
    }
)


def _write_input(tmp_path: Path) -> Path:
    sections = [
        {"title": "GPT-5 released", "url": "https://a.com", "body": "OpenAI's new model."},
        {"title": "New JS framework", "url": "https://b.com", "body": "Yet another framework."},
    ]
    return write_sections(tmp_path / "in.md", sections)


@pytest.mark.asyncio
async def test_filters_below_threshold_articles(tmp_path: Path) -> None:
    agent = NewsFilterAgent(relevance_threshold=6)
    input_path = _write_input(tmp_path)
    output_path = tmp_path / "out.md"

    with patch.object(
        agent,
        "_call_llm",
        AsyncMock(side_effect=[RELEVANT_JUDGMENT, NOT_RELEVANT_JUDGMENT]),
    ):
        result = await agent.execute(str(input_path), str(output_path))

    assert result["total_input"] == 2
    assert result["total_output"] == 1
    assert result["filtered_articles"][0]["title"] == "GPT-5 released"

    saved = load_sections(output_path)
    assert len(saved) == 1
    assert saved[0]["title"] == "GPT-5 released"
    assert saved[0]["relevance_score"] == "9"


@pytest.mark.asyncio
async def test_malformed_llm_response_degrades_to_not_relevant(tmp_path: Path) -> None:
    agent = NewsFilterAgent()
    input_path = _write_input(tmp_path)
    output_path = tmp_path / "out.md"

    with patch.object(agent, "_call_llm", AsyncMock(return_value="not json at all")):
        result = await agent.execute(str(input_path), str(output_path))

    assert result["total_output"] == 0


@pytest.mark.asyncio
async def test_strips_markdown_code_fences_from_response(tmp_path: Path) -> None:
    agent = NewsFilterAgent(relevance_threshold=6)
    input_path = _write_input(tmp_path)
    output_path = tmp_path / "out.md"

    fenced = f"```json\n{RELEVANT_JUDGMENT}\n```"
    with patch.object(agent, "_call_llm", AsyncMock(return_value=fenced)):
        result = await agent.execute(str(input_path), str(output_path))

    assert result["total_output"] == 2
