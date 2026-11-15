"""Tests for GitHubTrendingFetcher, with the HTTP layer mocked out."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.transformers.article_transformer import ArticleTransformer

SEARCH_RESPONSE = {
    "items": [
        {
            "full_name": "someone/cool-project",
            "html_url": "https://github.com/someone/cool-project",
            "description": "A cool project",
            "stargazers_count": 100,
            "created_at": "2026-01-01T00:00:00Z",
        },
        # No html_url -> should be dropped by the transformer.
        {"full_name": "broken/entry"},
    ]
}


def _make_mock_session() -> MagicMock:
    response = MagicMock()
    response.json = AsyncMock(return_value=SEARCH_RESPONSE)

    get_cm = MagicMock()
    get_cm.__aenter__ = AsyncMock(return_value=response)
    get_cm.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=get_cm)

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    return session_cm


@pytest.mark.asyncio
async def test_fetch_articles_returns_valid_repos_only() -> None:
    fetcher = GitHubTrendingFetcher(ArticleTransformer(), storage=MagicMock(), limit=5)

    with patch(
        "src.fetchers.github_trending_fetcher.aiohttp.ClientSession",
        return_value=_make_mock_session(),
    ):
        articles = await fetcher.fetch_articles()

    assert len(articles) == 1
    assert articles[0].title == "someone/cool-project"
    assert articles[0].source == "github"


def test_get_source_name() -> None:
    fetcher = GitHubTrendingFetcher(ArticleTransformer(), storage=MagicMock())
    assert fetcher.get_source_name() == "github"
