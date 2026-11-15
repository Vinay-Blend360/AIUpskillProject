"""Abstract base for news fetchers (Open/Closed + Template Method).

New sources are added by subclassing ``BaseFetcher`` and implementing
``fetch_articles``/``get_source_name`` — the orchestrator, storage, and
existing fetchers never need to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer


class BaseFetcher(ABC):
    """Common shape for every news source."""

    def __init__(self, transformer: ArticleTransformer, storage: ArticleStorage) -> None:
        self.transformer = transformer
        self.storage = storage

    @abstractmethod
    async def fetch_articles(self) -> list[Article]:
        """Fetch and transform this source's articles."""
        raise NotImplementedError

    @abstractmethod
    def get_source_name(self) -> str:
        """A short, filesystem-safe name identifying this source (e.g. 'hackernews')."""
        raise NotImplementedError

    async def fetch_and_save(self) -> list[Article]:
        """Template method: fetch this source's articles, then persist them."""
        articles = await self.fetch_articles()
        if articles:
            self.storage.save(articles, f"{self.get_source_name()}_articles.md")
        return articles
