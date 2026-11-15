"""Article data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Article:
    """Represents a single news article fetched from a source."""

    title: str
    url: str
    published_at: datetime
    source: str
    summary: str = ""
    score: int = 0

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Article must have a title")
        if not self.url:
            raise ValueError("Article must have a URL")

    def to_markdown(self) -> str:
        """Render the article as a markdown section."""
        return f"""## {self.title}

**Source:** {self.source}
**URL:** {self.url}
**Published:** {self.published_at.strftime('%Y-%m-%d %H:%M')}
**Score:** {self.score}

{self.summary}
"""
