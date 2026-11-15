"""Tests for the Factory and Strategy patterns introduced in Milestone 2."""

import asyncio
import time
from unittest.mock import MagicMock

import pytest

from src.factories.fetcher_factory import FetcherFactory
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.strategies.rate_limit_strategy import SemaphoreStrategy, TokenBucketStrategy
from src.transformers.article_transformer import ArticleTransformer


class _FakeFetcher:
    def __init__(self, transformer, storage, **kwargs) -> None:
        self.transformer = transformer
        self.storage = storage
        self.kwargs = kwargs

    def get_source_name(self) -> str:
        return "fake"


def test_factory_creates_registered_fetchers() -> None:
    transformer = ArticleTransformer()
    storage = MagicMock()

    assert isinstance(FetcherFactory.create("hackernews", transformer, storage), HackerNewsFetcher)
    assert isinstance(FetcherFactory.create("github", transformer, storage), GitHubTrendingFetcher)
    assert isinstance(
        FetcherFactory.create("rss", transformer, storage, feed_url="https://x.com/feed"),
        RSSFetcher,
    )


def test_factory_rejects_unknown_type() -> None:
    with pytest.raises(ValueError):
        FetcherFactory.create("carrier-pigeon", ArticleTransformer(), MagicMock())


def test_factory_register_adds_new_type() -> None:
    FetcherFactory.register("fake", _FakeFetcher)
    try:
        fetcher = FetcherFactory.create("fake", ArticleTransformer(), MagicMock())
        assert isinstance(fetcher, _FakeFetcher)
        assert "fake" in FetcherFactory.get_available_types()
    finally:
        del FetcherFactory._fetchers["fake"]


@pytest.mark.asyncio
async def test_semaphore_strategy_caps_concurrency() -> None:
    limiter = SemaphoreStrategy(max_concurrent=2)
    active = 0
    max_active = 0

    async def task() -> None:
        nonlocal active, max_active
        async with limiter:
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.02)
            active -= 1

    await asyncio.gather(*[task() for _ in range(6)])
    assert max_active <= 2


@pytest.mark.asyncio
async def test_token_bucket_strategy_limits_rate() -> None:
    limiter = TokenBucketStrategy(rate=2, per=1.0)

    start = time.monotonic()
    for _ in range(4):
        async with limiter:
            pass
    elapsed = time.monotonic() - start

    # 4 ops at 2/sec should take at least ~1 second (first 2 are free).
    assert elapsed >= 0.9
