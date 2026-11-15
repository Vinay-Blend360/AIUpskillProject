"""Tests for MarkdownStorage."""

from datetime import datetime
from pathlib import Path

from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage


def _make_article(i: int = 0) -> Article:
    return Article(
        title=f"Article {i}",
        url=f"https://test{i}.com",
        published_at=datetime.now(),
        source="test",
    )


def test_storage_creates_base_path(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "articles"
    MarkdownStorage(str(target))
    assert target.exists()


def test_storage_save_writes_file(tmp_path: Path) -> None:
    storage = MarkdownStorage(str(tmp_path))

    path = storage.save([_make_article()], "test.md")

    assert path.exists()
    content = path.read_text()
    assert "Article 0" in content
    assert "https://test0.com" in content


def test_storage_save_multiple_articles(tmp_path: Path) -> None:
    storage = MarkdownStorage(str(tmp_path))
    articles = [_make_article(i) for i in range(5)]

    path = storage.save(articles)
    content = path.read_text()

    assert "Article 0" in content
    assert "Article 4" in content
    assert "**Total Articles:** 5" in content


def test_storage_auto_generates_filename(tmp_path: Path) -> None:
    storage = MarkdownStorage(str(tmp_path))

    path = storage.save([_make_article()])

    assert path.parent == tmp_path
    assert path.suffix == ".md"
