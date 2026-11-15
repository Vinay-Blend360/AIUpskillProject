"""Fetch "trending" repositories from GitHub.

GitHub doesn't expose an official trending API, and scraping github.com/trending's
HTML is brittle (undocumented markup, against the spirit of their ToS for
automated access). Instead we approximate "trending" via the public Search API:
repositories created in the last week, sorted by stars. This is a documented,
stable, rate-limit-friendly endpoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import aiohttp

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer

SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubTrendingFetcher(BaseFetcher):
    """Fetches recently-created, highly-starred GitHub repositories."""

    def __init__(
        self,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
        limit: int = 25,
        lookback_days: int = 7,
    ) -> None:
        super().__init__(transformer, storage)
        self.limit = limit
        self.lookback_days = lookback_days

    def get_source_name(self) -> str:
        return "github"

    async def fetch_articles(self) -> list[Article]:
        since = (datetime.now() - timedelta(days=self.lookback_days)).strftime("%Y-%m-%d")
        params = {
            "q": f"created:>{since}",
            "sort": "stars",
            "order": "desc",
            "per_page": str(self.limit),
        }
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-upskill-news-pipeline",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(SEARCH_URL, params=params, headers=headers) as response:
                data = await response.json()

        repos = data.get("items", [])
        articles = [self.transformer.transform_github(repo) for repo in repos]
        return [a for a in articles if a is not None]
