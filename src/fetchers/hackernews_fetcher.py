"""Fetch top stories from the HackerNews API."""

from __future__ import annotations

import asyncio

import aiohttp

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.strategies.rate_limit_strategy import RateLimitStrategy, SemaphoreStrategy
from src.transformers.article_transformer import ArticleTransformer


class HackerNewsFetcher(BaseFetcher):
    """Fetches top stories from the public HackerNews API.

    API docs: https://github.com/HackerNews/API
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(
        self,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
        limit: int = 30,
        rate_limiter: RateLimitStrategy | None = None,
    ) -> None:
        super().__init__(transformer, storage)
        self.limit = limit
        self.rate_limiter = rate_limiter or SemaphoreStrategy(max_concurrent=10)

    def get_source_name(self) -> str:
        return "hackernews"

    async def fetch_articles(self) -> list[Article]:
        async with aiohttp.ClientSession() as session:
            story_ids = await self._fetch_top_story_ids(session)
            return await self._fetch_stories(session, story_ids[: self.limit])

    async def _fetch_top_story_ids(self, session: aiohttp.ClientSession) -> list[int]:
        url = f"{self.BASE_URL}/topstories.json"
        async with session.get(url) as response:
            return await response.json()

    async def _fetch_stories(
        self, session: aiohttp.ClientSession, story_ids: list[int]
    ) -> list[Article]:
        tasks = [self._fetch_story(session, story_id) for story_id in story_ids]
        stories = await asyncio.gather(*tasks)
        return [s for s in stories if s is not None]

    async def _fetch_story(self, session: aiohttp.ClientSession, story_id: int) -> Article | None:
        url = f"{self.BASE_URL}/item/{story_id}.json"

        try:
            async with self.rate_limiter:
                async with session.get(url) as response:
                    data = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

        return self.transformer.transform_hackernews(data)
