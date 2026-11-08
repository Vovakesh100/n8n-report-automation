# Running locally

1. Copy the variable names: `cp .env.example .env`. Fill in the values by hand in `.env`
   (bot token, chat id, time zone). `.env` is git-ignored; never commit it.
   The time zone is not chosen by this repo (open question Q1).
2. Start n8n: `docker compose up --build`. The first run builds a small image with `python3`.
   n8n state is stored in `./n8n_data`. Open http://localhost:5678.
3. In n8n, import `workflows/daily_report.json` (Workflows, Import from file).
4. No n8n credential is needed: the "Send Telegram" HTTP Request node reads
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from the environment (set in `.env`).
5. Run the workflow manually, or wait for the Schedule Trigger (09:00 every day,
   Europe/Chisinau). The Execute Command node runs
   `PYTHONPATH=/app/src python3 -m report.cli '<REPORT_CSV_PATH or /data/sample_sales.csv>'`;
   `./src` and `./data` are mounted read-only at `/app/src` and `/data`. Activate the
   workflow in n8n for the schedule to fire.
