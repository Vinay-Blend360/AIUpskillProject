"""Tests for DatabaseManager."""

from pathlib import Path

import pytest

from src.storage.db_manager import DatabaseManager


@pytest.mark.asyncio
async def test_initialize_creates_schema(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()

    assert (tmp_path / "test.db").exists()
    assert await db.query_articles() == []


@pytest.mark.asyncio
async def test_insert_and_query(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()

    inserted = await db.insert_article(
        {
            "title": "GPT-5 released",
            "url": "https://a.com",
            "source": "hackernews",
            "published_at": "2026-01-01T00:00:00",
            "summary": "A new model.",
            "score": 100,
            "relevance_score": 9,
        }
    )
    assert inserted is True

    articles = await db.query_articles()
    assert len(articles) == 1
    assert articles[0]["title"] == "GPT-5 released"


@pytest.mark.asyncio
async def test_duplicate_url_is_rejected_not_raised(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    article = {
        "title": "A",
        "url": "https://dup.com",
        "source": "hackernews",
        "published_at": "2026-01-01T00:00:00",
    }

    assert await db.insert_article(article) is True
    assert await db.insert_article(article) is False
    assert len(await db.query_articles()) == 1


@pytest.mark.asyncio
async def test_query_filters_by_source(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(
        {"title": "A", "url": "https://a.com", "source": "hackernews", "published_at": "2026-01-01"}
    )
    await db.insert_article(
        {"title": "B", "url": "https://b.com", "source": "rss", "published_at": "2026-01-01"}
    )

    hn_only = await db.query_articles(source="hackernews")
    assert len(hn_only) == 1
    assert hn_only[0]["source"] == "hackernews"


@pytest.mark.asyncio
async def test_search_articles_matches_title_and_summary(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(
        {
            "title": "Transformers explained",
            "url": "https://a.com",
            "source": "hackernews",
            "published_at": "2026-01-01",
            "summary": "Deep dive.",
        }
    )
    await db.insert_article(
        {
            "title": "Unrelated",
            "url": "https://b.com",
            "source": "rss",
            "published_at": "2026-01-01",
            "summary": "Nothing to do with AI.",
        }
    )

    results = await db.search_articles("transformers")
    assert len(results) == 1
    assert results[0]["title"] == "Transformers explained"


@pytest.mark.asyncio
async def test_get_sources_returns_distinct_sorted(tmp_path: Path) -> None:
    db = DatabaseManager(str(tmp_path / "test.db"))
    await db.initialize()
    await db.insert_article(
        {"title": "A", "url": "https://a.com", "source": "rss", "published_at": "2026-01-01"}
    )
    await db.insert_article(
        {"title": "B", "url": "https://b.com", "source": "hackernews", "published_at": "2026-01-01"}
    )
    await db.insert_article(
        {"title": "C", "url": "https://c.com", "source": "rss", "published_at": "2026-01-01"}
    )

    assert await db.get_sources() == ["hackernews", "rss"]
