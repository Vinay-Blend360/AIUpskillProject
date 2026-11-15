"""End-to-end pipeline: fetch articles, then filter them for AI/ML relevance."""

from __future__ import annotations

import asyncio
import sys

from src.agents.news_filter_agent import NewsFilterAgent
from src.main import build_orchestrator

FETCHED_PATH = "data/articles/all_articles.md"
FILTERED_PATH = "data/articles/filtered_articles.md"


async def main() -> int:
    orchestrator = build_orchestrator()
    articles = await orchestrator.fetch_all()
    print(f"✅ Fetched {len(articles)} articles")

    if not articles:
        print("No articles fetched; nothing to filter.")
        return 0

    filter_agent = NewsFilterAgent()
    result = await filter_agent.execute(FETCHED_PATH, FILTERED_PATH)
    print(
        f"\U0001f9e0 Filtered {result['total_input']} -> {result['total_output']} relevant articles"
    )
    print(f"\U0001f4c1 Saved to: {FILTERED_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
