"""Persist articles to markdown files on disk."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.models.article import Article
from src.storage.base_storage import ArticleStorage


class MarkdownStorage(ArticleStorage):
    """Writes a list of articles to a single markdown file."""

    def __init__(self, base_path: str = "data/articles") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, articles: list[Article], filename: str | None = None) -> Path:
        """Write ``articles`` to ``filename`` under ``base_path``.

        Returns the path to the file that was written.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"articles_{timestamp}.md"

        filepath = self.base_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# News Articles\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Articles:** {len(articles)}\n\n")
            f.write("---\n\n")

            for article in articles:
                f.write(article.to_markdown())
                f.write("\n---\n\n")

        return filepath
