"""Tests for ArticleTransformer."""

import feedparser

from src.transformers.article_transformer import ArticleTransformer

transformer = ArticleTransformer()


def test_transform_hackernews_skips_urlless_items() -> None:
    assert transformer.transform_hackernews({"title": "Ask HN", "time": 1700000000}) is None


def test_transform_hackernews_builds_article() -> None:
    article = transformer.transform_hackernews(
        {"title": "Story", "url": "https://a.com", "time": 1700000000, "score": 5}
    )
    assert article is not None
    assert article.source == "hackernews"
    assert article.score == 5


def test_transform_rss_skips_entries_without_link() -> None:
    entry = feedparser.FeedParserDict(title="No link")
    assert transformer.transform_rss(entry) is None


def test_transform_rss_strips_html_from_summary() -> None:
    entry = feedparser.FeedParserDict(
        title="Entry", link="https://example.com/1", summary="<p>Hello <b>world</b></p>"
    )
    article = transformer.transform_rss(entry)
    assert article is not None
    assert article.summary == "Hello world"


def test_transform_github_skips_items_without_url() -> None:
    assert transformer.transform_github({"full_name": "x/y"}) is None


def test_transform_github_builds_article() -> None:
    repo = {
        "full_name": "octocat/hello-world",
        "html_url": "https://github.com/octocat/hello-world",
        "description": "A demo repo",
        "stargazers_count": 42,
        "created_at": "2026-01-01T00:00:00Z",
    }
    article = transformer.transform_github(repo)
    assert article is not None
    assert article.source == "github"
    assert article.score == 42
    assert article.summary == "A demo repo"
