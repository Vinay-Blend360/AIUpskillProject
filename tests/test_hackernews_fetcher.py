"""Tests for HackerNewsFetcher, with the HTTP layer mocked out."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.models.article import Article
from src.transformers.article_transformer import ArticleTransformer

STORY_IDS = [1, 2, 3]

STORIES = {
    1: {"title": "Story 1", "url": "https://a.com", "time": 1700000000, "score": 10},
    2: {"title": "Story 2", "url": "https://b.com", "time": 1700000100, "score": 20},
    # Story 3 is an "Ask HN" with no external url and should be skipped.
    3: {"title": "Ask HN: question", "time": 1700000200, "score": 5},
}


def _make_mock_session() -> MagicMock:
    """Build a mock aiohttp.ClientSession whose .get() resolves per-URL."""

    def get(url: str) -> MagicMock:
        response = MagicMock()
        if url.endswith("topstories.json"):
            response.json = AsyncMock(return_value=STORY_IDS)
        else:
            story_id = int(url.rsplit("/", 1)[-1].replace(".json", ""))
            response.json = AsyncMock(return_value=STORIES[story_id])

        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    session = MagicMock()
    session.get = MagicMock(side_effect=get)

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    return session_cm


@pytest.mark.asyncio
async def test_fetch_returns_articles_and_skips_urlless_stories() -> None:
    fetcher = HackerNewsFetcher(ArticleTransformer(), storage=MagicMock(), limit=3)

    with patch(
        "src.fetchers.hackernews_fetcher.aiohttp.ClientSession",
        return_value=_make_mock_session(),
    ):
        articles = await fetcher.fetch_articles()

    assert len(articles) == 2
    for article in articles:
        assert isinstance(article, Article)
        assert article.source == "hackernews"

    titles = {a.title for a in articles}
    assert titles == {"Story 1", "Story 2"}


@pytest.mark.asyncio
async def test_fetch_respects_limit() -> None:
    fetcher = HackerNewsFetcher(ArticleTransformer(), storage=MagicMock(), limit=1)

    with patch(
        "src.fetchers.hackernews_fetcher.aiohttp.ClientSession",
        return_value=_make_mock_session(),
    ):
        articles = await fetcher.fetch_articles()

    assert len(articles) == 1
    assert articles[0].title == "Story 1"
