"""Tests for the shared markdown section read/write format."""

from pathlib import Path

from src.storage.markdown_sections import load_sections, write_sections


def test_round_trip(tmp_path: Path) -> None:
    sections = [
        {"title": "First", "url": "https://a.com", "relevance_score": 8, "body": "Some reasoning."},
        {
            "title": "Second",
            "url": "https://b.com",
            "relevance_score": 3,
            "body": "Other reasoning.",
        },
    ]
    path = write_sections(tmp_path / "out.md", sections, header="# Header")

    loaded = load_sections(path)

    assert len(loaded) == 2
    assert loaded[0]["title"] == "First"
    assert loaded[0]["url"] == "https://a.com"
    assert loaded[0]["relevance_score"] == "8"
    assert loaded[0]["body"] == "Some reasoning."


def test_load_sections_reads_markdown_storage_output(tmp_path: Path) -> None:
    """MarkdownStorage.save() output must be readable by load_sections() too."""
    from datetime import datetime

    from src.models.article import Article
    from src.storage.markdown_storage import MarkdownStorage

    article = Article(
        title="An Article",
        url="https://example.com",
        published_at=datetime(2026, 1, 1, 12, 0),
        source="test",
        summary="A summary.",
    )
    storage = MarkdownStorage(str(tmp_path))
    path = storage.save([article], "articles.md")

    loaded = load_sections(path)

    assert len(loaded) == 1
    assert loaded[0]["title"] == "An Article"
    assert loaded[0]["url"] == "https://example.com"
    assert loaded[0]["body"] == "A summary."
