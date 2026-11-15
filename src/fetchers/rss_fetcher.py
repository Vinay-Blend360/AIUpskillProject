"""Fetch articles from an RSS feed."""

from __future__ import annotations

import asyncio

import feedparser

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class RSSFetcher(BaseFetcher):
    """Fetches and parses articles from a single RSS feed URL."""

    def __init__(
        self,
        feed_url: str,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
    ) -> None:
        super().__init__(transformer, storage)
        self.feed_url = feed_url

    def get_source_name(self) -> str:
        host = self.feed_url.split("//")[-1].split("/")[0]
        return f"rss_{host}"

    async def fetch_articles(self) -> list[Article]:
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)

        articles = []
        for entry in feed.entries:
            article = self.transformer.transform_rss(entry)
            if article is not None:
                articles.append(article)
        return articles
