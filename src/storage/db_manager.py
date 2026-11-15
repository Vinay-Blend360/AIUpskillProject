"""SQLite persistence layer for articles.

Uses the stdlib ``sqlite3`` module (synchronous) off the event loop via
``asyncio.to_thread`` rather than adding an ``aiosqlite`` dependency that
isn't in requirements.txt.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT NOT NULL,
    summary TEXT,
    score INTEGER DEFAULT 0,
    relevance_score INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_published ON articles(published_at);
"""


class DatabaseManager:
    """Async-friendly wrapper around a SQLite articles database."""

    def __init__(self, db_path: str = "data/articles.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(_SCHEMA)

    async def insert_article(self, article: dict) -> bool:
        """Insert one article. Returns False (without raising) on a duplicate URL."""
        return await asyncio.to_thread(self._insert_article_sync, article)

    def _insert_article_sync(self, article: dict) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO articles
                        (title, url, source, published_at, summary, score, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article["title"],
                        article["url"],
                        article["source"],
                        article["published_at"],
                        article.get("summary", ""),
                        article.get("score", 0),
                        article.get("relevance_score", 0),
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    async def query_articles(self, source: str | None = None, limit: int = 50) -> list[dict]:
        return await asyncio.to_thread(self._query_articles_sync, source, limit)

    def _query_articles_sync(self, source: str | None, limit: int) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if source:
                rows = conn.execute(
                    "SELECT * FROM articles WHERE source = ? ORDER BY id DESC LIMIT ?",
                    (source, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM articles ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(row) for row in rows]

    async def search_articles(self, query: str, limit: int = 20) -> list[dict]:
        return await asyncio.to_thread(self._search_articles_sync, query, limit)

    def _search_articles_sync(self, query: str, limit: int) -> list[dict]:
        needle = f"%{query.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM articles
                WHERE lower(title) LIKE ? OR lower(summary) LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (needle, needle, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    async def get_sources(self) -> list[str]:
        return await asyncio.to_thread(self._get_sources_sync)

    def _get_sources_sync(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT DISTINCT source FROM articles").fetchall()
            return sorted(row[0] for row in rows)
