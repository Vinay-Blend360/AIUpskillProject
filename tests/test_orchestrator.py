"""Tests for FetchOrchestrator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.article import Article
from src.orchestration.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage


def _article(source: str) -> Article:
    return Article(
        title=f"{source} article",
        url=f"https://{source}.example.com",
        published_at=datetime.now(),
        source=source,
    )


def _fake_fetcher(
    name: str, articles: list[Article] | None = None, error: Exception | None = None
) -> MagicMock:
    fetcher = MagicMock()
    fetcher.get_source_name.return_value = name
    if error is not None:
        fetcher.fetch_articles = AsyncMock(side_effect=error)
    else:
        fetcher.fetch_articles = AsyncMock(return_value=articles or [])
    return fetcher


@pytest.mark.asyncio
async def test_fetch_all_combines_sources_and_saves(tmp_path: Path) -> None:
    fetchers = [
        _fake_fetcher("hackernews", [_article("hackernews")]),
        _fake_fetcher("rss", [_article("rss")]),
    ]
    orchestrator = FetchOrchestrator(fetchers, storage=MarkdownStorage(str(tmp_path)))

    articles = await orchestrator.fetch_all()

    assert len(articles) == 2
    sources = {a.source for a in articles}
    assert sources == {"hackernews", "rss"}

    saved_file = tmp_path / "all_articles.md"
    assert saved_file.exists()


@pytest.mark.asyncio
async def test_fetch_all_tolerates_source_failure(tmp_path: Path) -> None:
    fetchers = [
        _fake_fetcher("hackernews", error=RuntimeError("boom")),
        _fake_fetcher("rss", [_article("rss")]),
    ]
    orchestrator = FetchOrchestrator(fetchers, storage=MarkdownStorage(str(tmp_path)))

    articles = await orchestrator.fetch_all()

    assert all(a.source == "rss" for a in articles)
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_fetch_all_is_injected_not_constructed(tmp_path: Path) -> None:
    """Orchestrator must not know how to build fetchers/storage itself (DIP)."""
    fetchers = [_fake_fetcher("hackernews", [_article("hackernews")])]
    storage = MagicMock()
    orchestrator = FetchOrchestrator(fetchers, storage=storage)

    await orchestrator.fetch_all()

    storage.save.assert_called_once()
