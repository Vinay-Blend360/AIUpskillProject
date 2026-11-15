# Milestone 2: SOLID Design Decisions

How the Milestone 1 fetcher code was refactored, and why.

## Single Responsibility

Each fetcher used to fetch raw data, transform it into `Article`s, *and* decide
how to persist it. That's three reasons to change. Responsibilities are now
split:

- **`ArticleTransformer`** (`src/transformers/article_transformer.py`) — maps
  one source's raw payload shape onto `Article`. One method per source
  (`transform_hackernews`, `transform_rss`, `transform_github`).
- **Fetchers** (`src/fetchers/*.py`) — retrieve raw data and hand it to the
  transformer. They no longer know what an `Article` field means.
- **`MarkdownStorage`** — persists `Article`s. Doesn't know where they came from.

## Open/Closed — adding GitHub Trending

`BaseFetcher` (`src/fetchers/base_fetcher.py`) defines the contract every
source implements: `fetch_articles()` and `get_source_name()`. Everything else
(storage, the orchestrator, the factory) depends on that abstraction.

`GitHubTrendingFetcher` was added as a new file implementing `BaseFetcher`.
**Zero lines changed** in `hackernews_fetcher.py`, `rss_fetcher.py`,
`base_fetcher.py`, `article_transformer.py` (beyond adding its own
`transform_github` method, which is additive), `markdown_storage.py`, or
`orchestrator.py`. It was wired in only by adding one line to
`FetcherFactory._fetchers` and one line in `src/main.py`.

GitHub has no official "trending" API. Rather than scrape `github.com/trending`
HTML (undocumented markup that breaks silently, and poor practice for
automated access), `GitHubTrendingFetcher` uses the public Search API
(`repos created in the last week, sorted by stars`) as a stable proxy for
"trending."

## Liskov Substitution

All three fetchers are interchangeable through the `BaseFetcher` interface —
same call shape (`fetch_articles()` returns `list[Article]`,
`get_source_name()` returns `str`), same behavioral contract (never raises for
"no results," returns `[]` instead). `tests/test_substitutability.py` drives
all three through one shared code path with no subclass-specific branching,
proving the substitution holds.

## Interface Segregation

Rather than invent speculative interfaces (`AuthenticatedFetcher`,
`PaginatedFetcher`, ...) that nothing implements yet, ISP is satisfied by
keeping `BaseFetcher` itself lean: two methods, both used by every
implementation. `ArticleStorage` (`src/storage/base_storage.py`) is a
separate, single-method interface rather than being folded into
`BaseFetcher` — a fetcher doesn't need to know how to save, and a storage
backend doesn't need to know how to fetch.

## Dependency Inversion

`FetchOrchestrator` (`src/orchestration/orchestrator.py`) takes its fetchers
and storage as constructor arguments — it has no idea whether a fetcher hits
an API, scrapes HTML, or parses RSS, and no idea whether storage is markdown
files or something else. `src/main.py` is the only place concrete classes get
instantiated and wired together (composition root).

## Design Patterns

- **Factory** (`src/factories/fetcher_factory.py`) — `FetcherFactory.create(name, ...)`
  maps a source-type string to a concrete fetcher class. New sources register
  via `FetcherFactory.register(name, cls)` instead of the caller needing to
  know every fetcher's import path.
- **Strategy** (`src/strategies/rate_limit_strategy.py`) — `RateLimitStrategy`
  is swappable per fetcher: `SemaphoreStrategy` caps concurrency (used by
  `HackerNewsFetcher`, which fans out many concurrent requests), `TokenBucketStrategy`
  caps throughput over time (useful against stricter per-second rate limits).
  Fetchers depend on the strategy interface, not a specific algorithm.
- **Template Method** (`src/fetchers/base_fetcher.py`) — `fetch_and_save()` is
  implemented once on `BaseFetcher` (fetch, then persist if non-empty) and
  reused by every subclass; subclasses only fill in `fetch_articles()` and
  `get_source_name()`.

## Trade-offs

- `GitHubTrendingFetcher` approximates "trending" via recency + stars rather
  than GitHub's actual (private, scraping-only) trending algorithm. Good
  enough for a news pipeline; not a faithful reproduction of the trending page.
- `TokenBucketStrategy` exists to demonstrate the Strategy pattern with a
  genuinely different algorithm, not because any current fetcher needs
  per-second throttling over concurrency capping — it isn't wired into any
  fetcher by default.
