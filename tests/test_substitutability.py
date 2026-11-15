"""Liskov substitution: every BaseFetcher subclass must be usable interchangeably.

The orchestrator (and anything else driving fetchers) only ever calls
`fetch_articles()` / `get_source_name()` / `fetch_and_save()`. If any
subclass needs special-casing to work, LSP is broken.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.models.article import Article
from src.transformers.article_transformer import ArticleTransformer


def _make_mock_session(responses: dict) -> MagicMock:
    def get(url: str, **kwargs) -> MagicMock:
        response = MagicMock()
        for marker, payload in responses.items():
            if marker in url:
                response.json = AsyncMock(return_value=payload)
                break
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
async def test_all_fetchers_implement_the_same_contract() -> None:
    transformer = ArticleTransformer()
    storage = MagicMock()

    hn = HackerNewsFetcher(transformer, storage, limit=1)
    hn_session = _make_mock_session(
        {"topstories": [1], "item": {"title": "S", "url": "https://a.com", "time": 0}}
    )

    gh = GitHubTrendingFetcher(transformer, storage, limit=1)
    gh_session = _make_mock_session({"search": {"items": []}})

    rss = RSSFetcher("https://example.com/feed.xml", transformer, storage)

    with patch("src.fetchers.hackernews_fetcher.aiohttp.ClientSession", return_value=hn_session):
        hn_articles = await hn.fetch_articles()

    with patch(
        "src.fetchers.github_trending_fetcher.aiohttp.ClientSession", return_value=gh_session
    ):
        gh_articles = await gh.fetch_articles()

    with patch("src.fetchers.rss_fetcher.feedparser.parse") as mock_parse:
        mock_parse.return_value.entries = []
        rss_articles = await rss.fetch_articles()

    for fetcher, articles in [(hn, hn_articles), (gh, gh_articles), (rss, rss_articles)]:
        assert isinstance(fetcher.get_source_name(), str)
        assert isinstance(articles, list)
        assert all(isinstance(a, Article) for a in articles)
