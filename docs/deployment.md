# Deployment

This runs as a set of standalone scripts against local files/SQLite — there's no server
to deploy, just a scheduled job.

## Local run

```bash
source venv/bin/activate
cp .env.example .env   # fill in LITELLM_MODEL + a provider API key
python -m src.orchestration.complete_pipeline
```

Outputs land in `data/articles/` (`all_articles.md`, `filtered_articles.md`, `summary.md`,
`newsletter.md`) and `data/articles.db` (SQLite).

## Environment variables

| Variable | Purpose |
|---|---|
| `LITELLM_MODEL` | LiteLLM model string, e.g. `gemini/gemini-flash-latest` or `claude-haiku-4-5-20251001` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | Whichever one matches `LITELLM_MODEL`'s provider |
| `ENVIRONMENT`, `LOG_LEVEL` | General config, see `.env.example` |

## Scheduling a daily run

**cron (macOS/Linux):**

```cron
0 7 * * * cd /path/to/AIUpskillProject && venv/bin/python -m src.orchestration.complete_pipeline >> logs/pipeline.log 2>&1
```

**Task Scheduler (Windows):** create a daily trigger that runs
`venv\Scripts\python.exe -m src.orchestration.complete_pipeline` with the working
directory set to the project root.

## Optional: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "src.orchestration.complete_pipeline"]
```

Mount `data/` as a volume so articles/the SQLite DB persist across container runs, and
pass `LITELLM_MODEL`/the provider API key as environment variables (`--env-file .env`)
rather than baking them into the image.

## Monitoring

There's no dashboard — tail the log file from the cron job above, or check:

```bash
ls -la data/articles/          # confirm today's files were written
sqlite3 data/articles.db "select source, count(*) from articles group by source;"
```

## Running the MCP server standalone

```bash
python -m src.mcp_servers.database_server
```

Talks stdio-JSONRPC, so it's meant to be spawned by an MCP client (see
`src/skills/search_skill.py` for the `stdio_client`/`ClientSession` pattern), not run
interactively.

## Troubleshooting

- **SSL cert errors on macOS calling HackerNews/GitHub/the LLM provider:** the
  python.org installer doesn't wire up a CA bundle automatically. Run
  `/Applications/Python 3.X/Install Certificates.command` once.
- **LiteLLM `NotFoundError` / model not found:** the pinned model string may have been
  deprecated by the provider. Check `LITELLM_MODEL` against the provider's current
  model list.
- **Empty `filtered_articles.md`:** check `NewsFilterAgent.relevance_threshold` (default
  6/10) isn't filtering out everything for a quiet news day — that's expected, not a bug.
