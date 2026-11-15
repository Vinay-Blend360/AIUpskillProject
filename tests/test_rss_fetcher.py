"""Tests for RSSFetcher, with feedparser mocked out."""

import time
from unittest.mock import MagicMock, patch

import feedparser
import pytest

from src.fetchers.rss_fetcher import RSSFetcher
from src.models.article import Article
from src.transformers.article_transformer import ArticleTransformer


def _fake_feed() -> feedparser.FeedParserDict:
    feed = feedparser.FeedParserDict()
    feed.entries = [
        feedparser.FeedParserDict(
            title="Entry 1",
            link="https://example.com/1",
            summary="<p>Hello <b>world</b></p>",
            published_parsed=time.gmtime(1700000000),
        ),
        feedparser.FeedParserDict(
            title="Entry 2",
            link="https://example.com/2",
            description="Plain summary",
        ),
        # Entries without a link should be dropped.
        feedparser.FeedParserDict(title="No link"),
    ]
    return feed


@pytest.mark.asyncio
async def test_fetch_parses_entries_and_strips_html() -> None:
    fetcher = RSSFetcher("https://example.com/feed.xml", ArticleTransformer(), storage=MagicMock())

    with patch("src.fetchers.rss_fetcher.feedparser.parse", return_value=_fake_feed()):
        articles = await fetcher.fetch_articles()

    assert len(articles) == 2
    for article in articles:
        assert isinstance(article, Article)
        assert article.source == "rss"

    first = next(a for a in articles if a.url == "https://example.com/1")
    assert first.summary == "Hello world"

    second = next(a for a in articles if a.url == "https://example.com/2")
    assert second.summary == "Plain summary"
