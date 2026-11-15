"""Tests for SummarizerAgent."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.summarizer_agent import SummarizerAgent
from src.storage.markdown_sections import load_sections, write_sections


@pytest.mark.asyncio
async def test_groups_articles_by_topic_and_summarizes(tmp_path: Path) -> None:
    input_path = write_sections(
        tmp_path / "filtered.md",
        [
            {"title": "A", "key_topics": "LLMs, GPT", "body": "reasoning A"},
            {"title": "B", "key_topics": "LLMs", "body": "reasoning B"},
            {"title": "C", "key_topics": "Computer Vision", "body": "reasoning C"},
        ],
    )
    output_path = tmp_path / "summary.md"
    agent = SummarizerAgent()

    with patch.object(agent, "_call_llm", AsyncMock(return_value="- bullet one\n- bullet two")):
        result = await agent.execute(str(input_path), str(output_path))

    topics = {s["topic"] for s in result["summaries"]}
    assert topics == {"LLMs", "Computer Vision"}

    saved = load_sections(output_path)
    assert len(saved) == 2
    assert all(s["body"] for s in saved)


@pytest.mark.asyncio
async def test_articles_without_topic_fall_back_to_general(tmp_path: Path) -> None:
    input_path = write_sections(tmp_path / "filtered.md", [{"title": "A", "body": "reasoning"}])
    agent = SummarizerAgent()

    with patch.object(agent, "_call_llm", AsyncMock(return_value="summary")):
        result = await agent.execute(str(input_path), str(tmp_path / "summary.md"))

    assert result["summaries"][0]["topic"] == "General"
