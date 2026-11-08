# Open questions

Agents write questions here instead of deciding. The owner answers in this file or in chat.

## Answered

1. **Send time and time zone:** 09:00, Europe/Chisinau (owner decision, T10).
2. **Telegram chat id:** set by the owner in `.env` (not committed). Agents never read or print it.
3. **CSV source:** local folder, `/data/sample_sales.csv` by default (decided by tech lead, D1).
4. **Date without orders:** the line `<date>: no sales` (owner decision, T11).
5. **Top product:** by revenue (decided by tech lead, D2).
6. **Telegram token:** set by the owner in `.env` (not committed). Agents never read or print it.
7. **Execute Command:** runs `python3` from the n8n image, no `uv` (T7 decision in `docs/DECISIONS.md`). Needs `NODES_EXCLUDE=[]`, which `docker-compose.yml` sets.
8. **Manual verification (Docker, n8n, Telegram):** done by the owner on 2026-11-08. Manual run sent the report; a scheduled run was also checked. Steps are in `docs/RUN.md`, Owner checklist.

## Still open

- **Report for "yesterday with no data":** the workflow passes no `--from`/`--to`, so a missing day at the end of the CSV is not shown as `no sales`. Changing the command is a separate task (T11 risk).
- **Execution data storage:** set to `none` in `docker-compose.yml` (T14). Keep it, or turn it on to inspect past runs in the n8n UI? Owner decision.
- **Demo data:** the workflow reads `sample_sales.csv`, which is synthetic. A real CSV needs `REPORT_CSV_PATH` in `.env` and the container recreated.
- **Activation error seen once:** the first publish failed with "Invalid cron expression" for the Schedule Trigger. The next publish worked. The cause is not known; the timezone variables in `.env` were empty at that moment.
