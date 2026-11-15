"""Entry point: fetch news from all sources and save to markdown."""

from __future__ import annotations

import asyncio
import sys

from src.factories.fetcher_factory import FetcherFactory
from src.orchestration.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer

RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
]


def build_orchestrator() -> FetchOrchestrator:
    transformer = ArticleTransformer()
    storage = MarkdownStorage()

    fetchers = [FetcherFactory.create("hackernews", transformer, storage, limit=30)]
    fetchers.extend(
        FetcherFactory.create("rss", transformer, storage, feed_url=feed_url)
        for feed_url in RSS_FEEDS
    )
    fetchers.append(FetcherFactory.create("github", transformer, storage, limit=25))

    return FetchOrchestrator(fetchers, storage)


async def main() -> int:
    orchestrator = build_orchestrator()
    try:
        articles = await orchestrator.fetch_all()
    except Exception as exc:  # noqa: BLE001 - top-level entry point
        print(f"❌ Error: {exc}")
        return 1

    print(f"✅ Fetched {len(articles)} articles total")
    print("\U0001f4c1 Saved to: data/articles/all_articles.md")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
