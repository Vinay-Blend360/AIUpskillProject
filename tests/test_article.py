"""Tests for the Article model."""

from datetime import datetime

import pytest

from src.models.article import Article


def test_article_creation(sample_article_kwargs: dict) -> None:
    article = Article(**sample_article_kwargs)
    assert article.title == sample_article_kwargs["title"]
    assert article.url == sample_article_kwargs["url"]
    assert article.source == "test"
    assert article.score == 0


def test_article_requires_title(sample_article_kwargs: dict) -> None:
    sample_article_kwargs["title"] = ""
    with pytest.raises(ValueError):
        Article(**sample_article_kwargs)


def test_article_requires_url(sample_article_kwargs: dict) -> None:
    sample_article_kwargs["url"] = ""
    with pytest.raises(ValueError):
        Article(**sample_article_kwargs)


def test_article_to_markdown(sample_article_kwargs: dict) -> None:
    sample_article_kwargs["summary"] = "A test summary."
    article = Article(**sample_article_kwargs)

    md = article.to_markdown()

    assert article.title in md
    assert article.url in md
    assert "A test summary." in md
    assert "test" in md


def test_article_published_at_formatting(sample_article_kwargs: dict) -> None:
    sample_article_kwargs["published_at"] = datetime(2026, 3, 5, 9, 30)
    article = Article(**sample_article_kwargs)

    assert "2026-03-05 09:30" in article.to_markdown()
