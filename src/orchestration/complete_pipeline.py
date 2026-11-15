"""Full pipeline: fetch -> persist -> filter -> summarize -> write newsletter."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import asdict

from src.agents.news_filter_agent import NewsFilterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.writer_agent import WriterAgent
from src.main import build_orchestrator
from src.storage.db_manager import DatabaseManager

FETCHED_PATH = "data/articles/all_articles.md"
FILTERED_PATH = "data/articles/filtered_articles.md"
SUMMARY_PATH = "data/articles/summary.md"
NEWSLETTER_PATH = "data/articles/newsletter.md"


async def run_pipeline() -> dict:
    orchestrator = build_orchestrator()
    articles = await orchestrator.fetch_all()
    print(f"✅ Fetched {len(articles)} articles")

    db = DatabaseManager()
    await db.initialize()
    for article in articles:
        record = asdict(article)
        record["published_at"] = article.published_at.isoformat()
        await db.insert_article(record)
    print(f"\U0001f5c4️  Persisted articles to {db.db_path}")

    if not articles:
        return {"articles": 0}

    filter_result = await NewsFilterAgent().execute(FETCHED_PATH, FILTERED_PATH)
    print(
        f"\U0001f9e0 Filtered {filter_result['total_input']} -> "
        f"{filter_result['total_output']} relevant articles"
    )

    if filter_result["total_output"] == 0:
        return {"articles": len(articles), "filtered": 0}

    await SummarizerAgent().execute(FILTERED_PATH, SUMMARY_PATH)
    print(f"\U0001f4dd Summarized topics -> {SUMMARY_PATH}")

    await WriterAgent().execute(SUMMARY_PATH, NEWSLETTER_PATH)
    print(f"\U0001f4f0 Wrote newsletter -> {NEWSLETTER_PATH}")

    return {"articles": len(articles), "filtered": filter_result["total_output"]}


async def main() -> int:
    try:
        await run_pipeline()
    except Exception as exc:  # noqa: BLE001 - top-level entry point
        print(f"❌ Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
