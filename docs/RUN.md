# Running locally

1. Copy the variable names: `cp .env.example .env`. Fill in the values by hand in `.env`
   (bot token, chat id, time zone). `.env` is git-ignored; never commit it.
   The time zone is not chosen by this repo (open question Q1).
2. Start n8n: `docker compose up --build`. The first run builds a small image with `python3`.
   n8n state is stored in `./n8n_data`. Open http://localhost:5678.
3. In n8n, import `workflows/daily_report.json` (Workflows, Import from file).
4. Create a Telegram API credential in n8n with your bot token, select it in the
   "Send Telegram" node, and set the Chat ID there.
5. Run the workflow manually. The Execute Command node runs
   `PYTHONPATH=/app/src python3 -m report.cli /data/sample_sales.csv`; `./src` and `./data`
   are mounted read-only at `/app/src` and `/data`.
