"""Storage abstraction so fetchers and the orchestrator depend on an interface, not a concrete writer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.article import Article


class ArticleStorage(ABC):
    """Persists articles somewhere. Concrete backends decide the format and destination."""

    @abstractmethod
    def save(self, articles: list[Article], filename: str | None = None) -> Path:
        """Persist ``articles`` and return a path/identifier for what was written."""
        raise NotImplementedError
