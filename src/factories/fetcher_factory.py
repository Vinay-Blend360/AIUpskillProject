"""Factory for constructing fetchers by source name (Factory pattern).

Keeps "which fetcher class does this source name map to" in one place,
rather than scattered across orchestration/config code.
"""

from __future__ import annotations

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class FetcherFactory:
    """Builds ``BaseFetcher`` instances from a registered source-type name."""

    _fetchers: dict[str, type[BaseFetcher]] = {
        "hackernews": HackerNewsFetcher,
        "rss": RSSFetcher,
        "github": GitHubTrendingFetcher,
    }

    @classmethod
    def create(
        cls,
        source_type: str,
        transformer: ArticleTransformer,
        storage: ArticleStorage,
        **kwargs,
    ) -> BaseFetcher:
        """Instantiate the fetcher registered for ``source_type``.

        Extra ``kwargs`` (e.g. ``feed_url`` for ``'rss'``) are forwarded to
        the fetcher's constructor.
        """
        fetcher_class = cls._fetchers.get(source_type)
        if fetcher_class is None:
            raise ValueError(
                f"Unknown fetcher type: {source_type!r}. Available: {sorted(cls._fetchers)}"
            )
        return fetcher_class(transformer=transformer, storage=storage, **kwargs)

    @classmethod
    def register(cls, name: str, fetcher_class: type[BaseFetcher]) -> None:
        """Register a new fetcher type, e.g. from a plugin."""
        cls._fetchers[name] = fetcher_class

    @classmethod
    def get_available_types(cls) -> list[str]:
        return sorted(cls._fetchers)
