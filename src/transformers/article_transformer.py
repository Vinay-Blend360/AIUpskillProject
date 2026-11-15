"""Transform raw source payloads (HN API JSON, feedparser entries, GitHub API JSON) into Articles.

Extracted out of the fetchers (SRP): a fetcher's job is retrieving raw data,
not deciding how that data maps onto our domain model.
"""

from __future__ import annotations

import re
import time
from datetime import datetime

import feedparser

from src.models.article import Article

_TAG_RE = re.compile(r"<.*?>")


class ArticleTransformer:
    """Maps each source's raw payload shape onto the common Article model."""

    def transform_hackernews(self, data: dict) -> Article | None:
        """Transform a single HackerNews API item into an Article, or None to skip it."""
        if not data or not data.get("url"):
            return None

        return Article(
            title=data.get("title", "No Title"),
            url=data["url"],
            published_at=datetime.fromtimestamp(data.get("time", 0)),
            source="hackernews",
            summary=data.get("text", "")[:200],
            score=data.get("score", 0),
        )

    def transform_rss(self, entry: feedparser.FeedParserDict) -> Article | None:
        """Transform a single feedparser entry into an Article, or None to skip it."""
        url = entry.get("link", "")
        if not url:
            return None

        title = entry.get("title", "No Title")
        published_at = self._parse_rss_date(entry)
        summary = _TAG_RE.sub("", entry.get("summary", entry.get("description", "")))[:200]

        try:
            return Article(
                title=title,
                url=url,
                published_at=published_at,
                source="rss",
                summary=summary,
            )
        except ValueError:
            return None

    def transform_github(self, repo: dict) -> Article | None:
        """Transform a single GitHub search-API repository result into an Article."""
        url = repo.get("html_url", "")
        if not url:
            return None

        try:
            published_at = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        except (KeyError, ValueError):
            published_at = datetime.now()

        try:
            return Article(
                title=repo.get("full_name", "Unknown repository"),
                url=url,
                published_at=published_at,
                source="github",
                summary=(repo.get("description") or "")[:200],
                score=repo.get("stargazers_count", 0),
            )
        except ValueError:
            return None

    @staticmethod
    def _parse_rss_date(entry: feedparser.FeedParserDict) -> datetime:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed))
        return datetime.now()
