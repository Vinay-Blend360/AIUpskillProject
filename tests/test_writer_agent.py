"""Tests for WriterAgent."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.writer_agent import WriterAgent


@pytest.mark.asyncio
async def test_writer_produces_newsletter_file(tmp_path: Path) -> None:
    input_path = tmp_path / "summary.md"
    input_path.write_text("# Topic Summaries\n\n## LLMs\n\nSome summary text.\n")
    output_path = tmp_path / "newsletter.md"

    agent = WriterAgent()
    with patch.object(agent, "_call_llm", AsyncMock(return_value="# Daily AI Digest\n\nContent.")):
        result = await agent.execute(str(input_path), str(output_path))

    assert "Daily AI Digest" in result["newsletter"]
    content = output_path.read_text()
    assert "Daily AI Digest" in content
    assert "Generated" in content
