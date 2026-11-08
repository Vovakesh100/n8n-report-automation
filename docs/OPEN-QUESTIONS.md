# Open questions

Agents write questions here instead of deciding. The owner answers in this file or in chat.

1. What time should the daily report be sent, and in which time zone? Needed for the workflow trigger (T5).
2. Which Telegram chat id should receive the report? Needed for T5. Only a placeholder is committed.
3. Should the CSV file be read from a local folder, or from a URL? Default proposal: local folder. **Decided by tech lead: local folder** (see docs/DECISIONS.md D1).
4. What should the report show if a date has no orders: a line saying "no sales" or no line at all?
5. Should the top product be chosen by revenue or by quantity? Default proposal: revenue. **Decided by tech lead: revenue** (see docs/DECISIONS.md D2).

## Values the owner must set in `workflows/daily_report.json` (T5)

The committed workflow has a manual trigger only. No schedule and no real chat id are committed.

- Q1 (send time and time zone): add a Schedule Trigger node (or replace "Manual Trigger") with the chosen time, and set the workflow time zone in n8n Workflow Settings. Connect it to the "Read CSV" node.
- Q2 (chat id): in the "Send Telegram" node, replace `REPLACE_WITH_TELEGRAM_CHAT_ID` in the Chat ID field.
- Telegram credential: in the "Send Telegram" node, select your own Telegram API credential (bot token created in n8n, never committed). Placeholder name is `REPLACE_WITH_TELEGRAM_CREDENTIAL_NAME`.
- Paths: "Read CSV" and "Run Report CLI" use `/data/sample_sales.csv` (local folder, D1). Adjust to the mounted path. The Execute Command node needs `uv` and the project available where n8n runs.
- Q4 (no-orders display) is not handled: the message lists only dates present in the CLI output.

6. **Telegram credentials needed (blocks a real send for T5).** `.env` was created from `.env.example` and is git-ignored, but `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are empty. The owner must fill them in `.env` by hand and create the Telegram credential in n8n. Agents do not write these values.

7. T7 owner actions: none needed to decide. When running n8n yourself, make sure the container has `python3`, `./src` mounted at `/app/src`, `./data` mounted at `/data`, and `NODES_EXCLUDE=[]` set (T9 will provide this in docker-compose). Until then, the Execute Command node will not load in n8n 2.x. This replaces the earlier "needs uv" note in the T5 section.
