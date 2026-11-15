"""Coordinate fetching from multiple news sources concurrently."""

from __future__ import annotations

import asyncio

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage


class FetchOrchestrator:
    """Fetches from all injected sources concurrently and persists the combined results.

    Depends only on the ``BaseFetcher``/``ArticleStorage`` abstractions
    (Dependency Inversion) — it has no idea whether a fetcher hits an API,
    scrapes HTML, or parses RSS, and no idea whether storage is markdown,
    a database, or anything else.
    """

    def __init__(self, fetchers: list[BaseFetcher], storage: ArticleStorage) -> None:
        self.fetchers = fetchers
        self.storage = storage

    async def fetch_all(self) -> list[Article]:
        """Fetch from every source concurrently and persist the combined results."""
        results = await asyncio.gather(
            *(fetcher.fetch_articles() for fetcher in self.fetchers),
            return_exceptions=True,
        )

        all_articles: list[Article] = []
        for fetcher, result in zip(self.fetchers, results):
            if isinstance(result, BaseException):
                print(f"⚠️  {fetcher.get_source_name()} failed: {result}")
            else:
                all_articles.extend(result)

        if all_articles:
            self.storage.save(all_articles, "all_articles.md")

        return all_articles
