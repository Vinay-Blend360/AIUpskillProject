# AI Upskill Project

**Blend's AI engineering onboarding curriculum.** A 5-week self-paced project
that takes engineers from async Python through agents, MCP, and evaluation
by building a small AI-powered news pipeline end-to-end.

- **Time commitment:** 1–2 hours per evening, ~5 weeks (38–54 hours total)
- **Format:** Self-paced. Each milestone ends with a PR checkpoint reviewed by two peers.
- **Outcome:** A working multi-agent news pipeline with tests, evaluation, and docs.
- **Status:** All five milestones (M0–M5) are implemented in `src/` and covered by `tests/` — see
  [Running the pipeline](#running-the-pipeline) and [Evaluation](#evaluation) below.

---

## Where to start

1. Read [`docs/architecture/overview.md`](docs/architecture/overview.md) for the 20-min big-picture orientation.
2. Open [`docs/milestones/milestone-0-setup.md`](docs/milestones/milestone-0-setup.md) and follow it. It will get you to a working dev environment in one evening.
3. From there, milestones link to the next one in sequence.

---

## The 5-week arc

| Week | Milestone | What you build | Hours |
|------|-----------|----------------|-------|
| 0 (Evening 1) | [M0 — Setup](docs/milestones/milestone-0-setup.md) | Dev environment, API key, verify script passes | 1–2 |
| 1 | [M1 — Async News Fetcher](docs/milestones/milestone-1-async-fetcher.md) | Hacker News + RSS fetchers, orchestrator, rate limiting, tests | 6–8 |
| 2 | [M2 — SOLID Refactoring](docs/milestones/milestone-2-solid-refactoring.md) | All five SOLID principles applied; add GitHub Trending with zero edits to existing code | 8–10 |
| 3 | [M3 — First Agent](docs/milestones/milestone-3-first-agent.md) | `NewsFilterAgent` via LiteLLM, prompt engineering, function calling | 8–10 |
| 4 | [M4 — MCP Pipeline](docs/milestones/milestone-4-mcp-pipeline.md) | Database MCP server, three-agent pipeline (Filter → Summarize → Write) | 10–14 |
| 5 | [M5 — Evaluation](docs/milestones/milestone-5-evaluation.md) | Golden dataset, accuracy/precision/recall/F1, project docs | 4–6 |

Full curriculum overview lives in [`docs/curriculum/overview.md`](docs/curriculum/overview.md).

---

## Tech stack

- **Python 3.11+** with async/await throughout
- **`aiohttp`** for concurrent HTTP, **`feedparser`** for RSS
- **LiteLLM** as the LLM provider abstraction — default model is set via `LITELLM_MODEL` in `.env`, swap to any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers) by changing that one line
- **MCP (Model Context Protocol)** for tool integration in Milestone 4
- **SQLite** (stdlib `sqlite3`, called off the event loop) for the database server in Milestone 4
- **pytest + pytest-asyncio** for tests
- **ruff** for formatting and linting

---

## Running the pipeline

```bash
# Fetch from all sources (HackerNews, RSS, GitHub) and save to data/articles/all_articles.md
python -m src.main

# Fetch, then filter for AI/ML relevance with NewsFilterAgent
python -m src.pipeline

# Full pipeline: fetch -> persist to SQLite -> filter -> summarize -> write newsletter
python -m src.orchestration.complete_pipeline
```

## Evaluation

`src/evaluation/evaluator.py` scores `NewsFilterAgent`'s relevance judgments against a
10-case labeled golden dataset (`data/evaluation/golden_dataset.json`) and reports
accuracy, precision, recall, and F1:

```bash
python -m src.evaluation.evaluator
# Report written to data/evaluation/evaluation_report.md
```

---

## Quickstart

```bash
git clone https://github.com/BLEND360/AIUpskillProject.git
cd AIUpskillProject

python3.11 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate            # Windows

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env               # then paste your API key
python scripts/verify_setup.py    # should print all ✅
```

Then open [`docs/milestones/milestone-0-setup.md`](docs/milestones/milestone-0-setup.md).

---

## Repository layout

```
AIUpskillProject/
├── README.md                  ← you are here
├── requirements.txt
├── .env.example
├── scripts/
│   └── verify_setup.py        # M0 Task 5 runs this
├── src/
│   ├── models/                # Article dataclass
│   ├── fetchers/               # HackerNews, RSS, GitHub + BaseFetcher (M1/M2)
│   ├── transformers/            # raw payload -> Article mapping (M2)
│   ├── strategies/              # rate-limiting strategies (M2)
│   ├── factories/                # FetcherFactory (M2)
│   ├── storage/                 # MarkdownStorage, markdown "sections" format, SQLite DatabaseManager
│   ├── agents/                  # NewsFilterAgent, SummarizerAgent, WriterAgent (M3/M4)
│   ├── tools/                   # calculator, web_search (function-calling demo, M3)
│   ├── mcp_servers/              # articles-database MCP server (M4)
│   ├── skills/                   # SearchSkill MCP client wrapper (M4)
│   ├── evaluation/                # FilterEvaluator (M5)
│   ├── orchestration/             # FetchOrchestrator, complete_pipeline (M1/M4)
│   ├── main.py                     # fetch-only entry point
│   └── pipeline.py                  # fetch + filter entry point
├── tests/                      # mirrors src/
├── data/
│   ├── articles/                # markdown output, created at runtime
│   └── evaluation/               # golden_dataset.json, evaluation_report.md
└── docs/
    ├── architecture/overview.md    # original curriculum overview
    ├── architecture.md              # implementation architecture (M5)
    ├── design-decisions.md          # SOLID/pattern rationale (M2)
    ├── deployment.md                 # running/scheduling/deploying (M5)
    ├── milestones/                   # M0 → M5 curriculum docs
    └── curriculum/                    # high-level curriculum docs
```

---

## Running tests

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

All external calls (HTTP, LLM, MCP transport) are mocked in the test suite, so it runs
offline and without API costs. Target: 60%+ coverage (currently well above that).

---

## How checkpoints work

Each milestone ends with a PR you open against your fork of this repo. Two
reviewers approve before you move on. PR templates and review criteria live
inside the relevant milestone doc.

---

## Questions

Ask in Slack: `#ai-upskill-cohort-[X]`
