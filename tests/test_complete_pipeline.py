"""Tests for the complete (fetch -> DB -> filter -> summarize -> write) pipeline wiring."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.models.article import Article
from src.orchestration import complete_pipeline


def _article() -> Article:
    return Article(
        title="Test",
        url="https://example.com",
        published_at=datetime.now(),
        source="hackernews",
    )


@pytest.mark.asyncio
async def test_run_pipeline_short_circuits_when_nothing_fetched() -> None:
    orchestrator = AsyncMock()
    orchestrator.fetch_all = AsyncMock(return_value=[])

    with (
        patch.object(complete_pipeline, "build_orchestrator", return_value=orchestrator),
        patch.object(complete_pipeline.DatabaseManager, "initialize", AsyncMock()),
        patch.object(complete_pipeline.DatabaseManager, "insert_article", AsyncMock()),
    ):
        result = await complete_pipeline.run_pipeline()

    assert result == {"articles": 0}


@pytest.mark.asyncio
async def test_run_pipeline_skips_summarize_write_when_nothing_relevant() -> None:
    orchestrator = AsyncMock()
    orchestrator.fetch_all = AsyncMock(return_value=[_article()])

    with (
        patch.object(complete_pipeline, "build_orchestrator", return_value=orchestrator),
        patch.object(complete_pipeline.DatabaseManager, "initialize", AsyncMock()),
        patch.object(complete_pipeline.DatabaseManager, "insert_article", AsyncMock()),
        patch.object(
            complete_pipeline.NewsFilterAgent,
            "execute",
            AsyncMock(return_value={"total_input": 1, "total_output": 0}),
        ) as mock_filter,
        patch.object(complete_pipeline.SummarizerAgent, "execute", AsyncMock()) as mock_summarize,
        patch.object(complete_pipeline.WriterAgent, "execute", AsyncMock()) as mock_write,
    ):
        result = await complete_pipeline.run_pipeline()

    assert result == {"articles": 1, "filtered": 0}
    mock_filter.assert_called_once()
    mock_summarize.assert_not_called()
    mock_write.assert_not_called()


@pytest.mark.asyncio
async def test_run_pipeline_runs_all_stages_when_articles_pass_filter() -> None:
    orchestrator = AsyncMock()
    orchestrator.fetch_all = AsyncMock(return_value=[_article()])

    with (
        patch.object(complete_pipeline, "build_orchestrator", return_value=orchestrator),
        patch.object(complete_pipeline.DatabaseManager, "initialize", AsyncMock()),
        patch.object(complete_pipeline.DatabaseManager, "insert_article", AsyncMock()),
        patch.object(
            complete_pipeline.NewsFilterAgent,
            "execute",
            AsyncMock(return_value={"total_input": 1, "total_output": 1}),
        ),
        patch.object(complete_pipeline.SummarizerAgent, "execute", AsyncMock()) as mock_summarize,
        patch.object(complete_pipeline.WriterAgent, "execute", AsyncMock()) as mock_write,
    ):
        result = await complete_pipeline.run_pipeline()

    assert result == {"articles": 1, "filtered": 1}
    mock_summarize.assert_called_once()
    mock_write.assert_called_once()
