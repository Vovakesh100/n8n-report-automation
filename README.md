# n8n Daily Sales Report

A small automation that reads sales data from a CSV file, computes a daily summary, and sends it to a Telegram chat every morning at 09:00 (Europe/Chisinau).

This is a portfolio demo project. It uses synthetic data only and is not client work.

## How it works

```
Schedule Trigger (09:00) / Manual Trigger
  -> Run Report CLI   (Python helper: CSV -> JSON summary per date)
  -> Format Message   (n8n code node: plain-text report, integer money formatting)
  -> Send Telegram    (HTTP request to the Telegram Bot API)
```

- `src/report/`: pure Python functions for the daily summary, plus a CLI that prints JSON. No I/O in the summary logic.
- `workflows/daily_report.json`: exported n8n workflow.
- `docker-compose.yml`: runs n8n 2.46.6 with the helper mounted into the container.
- Money is stored as integer cents. No floats are used for amounts.

## Requirements

- Docker Desktop
- A Telegram bot token (create one with @BotFather) and your chat id

## Run locally

1. Copy `.env.example` to `.env` and fill in the variables. The example file lists only the names:
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: required
   - `REPORT_FROM`, `REPORT_TO` (`YYYY-MM-DD`): optional date range
   - `REPORT_CSV_PATH`: optional, defaults to the sample file
2. Start n8n:
   ```
   docker compose up --build -d
   ```
3. Open http://localhost:5678, import `workflows/daily_report.json`, and run it manually.
4. Publish the workflow to enable the 09:00 schedule.

`docs/RUN.md` has the full owner checklist and notes on execution data settings.

## Tests and checks

```
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
```

## Data

`data/sample_sales.csv` is synthetic. The repository contains no real sales data, tokens or chat ids.

## Project docs

- `docs/TZ.md`: task description and acceptance criteria
- `docs/TASKS.md`: task list
- `docs/DECISIONS.md`: decisions and their reasons
- `docs/OPEN-QUESTIONS.md`: answered and open questions
