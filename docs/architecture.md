# Architecture

Implementation-level companion to [`docs/architecture/overview.md`](architecture/overview.md)
(the original curriculum overview) and [`docs/design-decisions.md`](design-decisions.md)
(the SOLID/pattern rationale). This doc describes the system as actually built.

## Components by milestone

| Milestone | Component | Module |
|---|---|---|
| M1 | `Article` model | `src/models/article.py` |
| M1/M2 | Fetchers (HackerNews, RSS, GitHub) + `BaseFetcher` | `src/fetchers/` |
| M2 | `ArticleTransformer` (raw payload -> `Article`) | `src/transformers/article_transformer.py` |
| M2 | `FetcherFactory` | `src/factories/fetcher_factory.py` |
| M2 | Rate-limit strategies | `src/strategies/rate_limit_strategy.py` |
| M1/M2 | `FetchOrchestrator` | `src/orchestration/orchestrator.py` |
| M1 | `MarkdownStorage` | `src/storage/markdown_storage.py` |
| M3 | `BaseAgent`, `NewsFilterAgent`, `EnhancedFilterAgent` | `src/agents/` |
| M3 | Function-calling tools | `src/tools/` |
| M4 | `SummarizerAgent`, `WriterAgent` | `src/agents/` |
| M4 | SQLite `DatabaseManager` | `src/storage/db_manager.py` |
| M4 | Articles-database MCP server | `src/mcp_servers/database_server.py` |
| M4 | `SearchSkill` (MCP client) | `src/skills/search_skill.py` |
| M4 | `complete_pipeline` (fetch -> DB -> filter -> summarize -> write) | `src/orchestration/complete_pipeline.py` |
| M5 | `FilterEvaluator` + golden dataset | `src/evaluation/`, `data/evaluation/` |

## Data flow

```
HackerNews ─┐
RSS         ├─► FetchOrchestrator ─► MarkdownStorage ─► all_articles.md
GitHub     ─┘                              │
                                            ▼
                                   NewsFilterAgent (LLM judgment)
                                            │
                                            ▼
                                  filtered_articles.md
                                            │
                                            ▼
                                   SummarizerAgent (LLM, grouped by topic)
                                            │
                                            ▼
                                      summary.md
                                            │
                                            ▼
                                     WriterAgent (LLM)
                                            │
                                            ▼
                                    newsletter.md

(in parallel) FetchOrchestrator output ──► DatabaseManager ──► SQLite ──► MCP server ──► SearchSkill
```

Articles flow as markdown between agent stages — human-readable, git-diffable, and a
natural shape for LLM context. `src/storage/markdown_sections.py` is the one module
that knows the `## Title` / `**Field:** value` / body shape, so every agent reads and
writes it the same way instead of each stage inventing its own parser. SQLite is a
parallel, queryable store underneath the markdown — not a replacement for it.

## Why LiteLLM + async LLM calls

Every agent's LLM call goes through `litellm.acompletion` (not the sync `completion`),
consistent with the rest of the codebase being async-first (`aiohttp`, `asyncio.gather`
in the orchestrator). This matters once a stage processes many articles concurrently —
a blocking call would stall the event loop for every other fetch/filter/summarize task.

## Why SQLite via stdlib `sqlite3`, not `aiosqlite`

`aiosqlite` isn't in `requirements.txt`, and the project's RSS fetcher already
establishes the pattern of running a sync library off the event loop via
`loop.run_in_executor` / `asyncio.to_thread` rather than adding an async-native
dependency. `DatabaseManager` follows the same pattern.

## Why GitHub Search API instead of scraping `github.com/trending`

GitHub has no official trending API. Scraping the HTML trending page is brittle
(undocumented, unversioned markup) and borderline for automated access. The Search API
(`repos created in the last week, sorted by stars`) is documented, stable, and a
reasonable proxy for "trending."

## Security notes

- The `calculator` tool evaluates LLM-generated expressions via an AST whitelist, never
  `eval()` — the expression is untrusted input.
- API keys live in `.env` (gitignored), never hardcoded.
- SQL queries in `DatabaseManager` are parameterized throughout — no string-built SQL.

## Known limitations / future enhancements

- `GitHubTrendingFetcher` approximates "trending" via recency + stars, not GitHub's
  actual (non-public) trending algorithm.
- `web_search` tool is stubbed (no search API key configured); swap in a real provider
  (Tavily, Brave Search, SerpAPI) to make `EnhancedFilterAgent` genuinely web-aware.
- The pipeline runs single-shot; there's no scheduler built in (see
  [`docs/deployment.md`](deployment.md) for how to add one with cron).
- `TokenBucketStrategy` exists to demonstrate the Strategy pattern but isn't wired into
  any fetcher by default — `SemaphoreStrategy` (concurrency cap) is what HackerNews uses.
