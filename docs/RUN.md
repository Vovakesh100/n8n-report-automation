# Running locally

1. Copy the variable names: `cp .env.example .env`. Fill in the values by hand in `.env`
   (bot token, chat id, time zone). `.env` is git-ignored; never commit it.
   The time zone is not chosen by this repo (open question Q1).
2. Start n8n: `docker compose up --build`. The first run builds a small image: pinned `n8nio/n8n` (Docker Hub) with `python3` copied from
   `python:3.12-alpine` (the n8n image has no `apk` or python).
   n8n state is stored in `./n8n_data`. Open http://localhost:5678.
3. In n8n, import `workflows/daily_report.json` (Workflows, Import from file).
4. No n8n credential is needed: the "Send Telegram" HTTP Request node reads
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from the environment (set in `.env`).
5. Run the workflow manually, or wait for the Schedule Trigger (09:00 every day,
   Europe/Chisinau). The Execute Command node runs
   `PYTHONPATH=/app/src python3 -m report.cli '<REPORT_CSV_PATH or /data/sample_sales.csv>'`;
   `./src` and `./data` are mounted read-only at `/app/src` and `/data`. Activate the
   workflow in n8n for the schedule to fire. Optional `REPORT_FROM` / `REPORT_TO` (YYYY-MM-DD) in `.env` add `--from` / `--to` to that command; empty means the whole file.

## Owner checklist
Verified in T12 with n8n 2.46.6 in Docker (CLI import and execute, fake token). Not verified there:
import through the UI, the 09:00 firing, a real Telegram send. Do these steps once:

1. Fill `.env` by hand (`cp .env.example .env`, then set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
   `GENERIC_TIMEZONE`, `TZ`). Run `docker compose up --build -d`, open http://localhost:5678, create the
   owner account, then Workflows, Import from file, choose `workflows/daily_report.json`.
2. Open the workflow, click "Execute workflow" (Manual Trigger). Run Report CLI and Format Message
   must turn green, then Send Telegram sends the message.
3. Check the Telegram chat: it must contain "Daily sales report" and one line per date
   (`2025-01-01: revenue 114.88, orders 7, top product gadget` for the sample data).
4. If it works, turn on the "Active" switch (top right) so the Schedule Trigger fires every day at
   09:00 (Europe/Chisinau). After the first 09:00, look at Executions to confirm the run.

The token and chat id are never printed in reports; agents do not read `.env`. Do not paste them
into issues or chat either.

Optional: the token is part of the Send Telegram request URL, so it can appear in stored execution
data (UI and `./n8n_data`). To avoid storing it, add to the `environment:` section of
`docker-compose.yml`: `EXECUTIONS_DATA_SAVE_ON_SUCCESS: none` and `EXECUTIONS_DATA_SAVE_ON_ERROR: none`
(the Executions list then keeps no data to inspect). If the token was ever shown or leaked, revoke it
in BotFather and set a new one.

## Execution data settings
`docker-compose.yml` sets `EXECUTIONS_DATA_SAVE_ON_SUCCESS: "none"` and
`EXECUTIONS_DATA_SAVE_ON_ERROR: "none"` (names and values checked against the n8n 2.46.6 image).

Effect: n8n does not store execution data for scheduled or finished runs. The Executions list in the
UI is empty or has no data to inspect, so debugging a past run is harder. The Telegram bot token is
part of the Send Telegram request URL, so it no longer lands in stored execution data (UI and
`./n8n_data`). It can still be seen in the live output of a manual run in the editor.

Undo: remove both lines from `docker-compose.yml`, or set both values to `all`, then run
`docker compose up -d` to recreate the container. Runs from then on are stored again.
