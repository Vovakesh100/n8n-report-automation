# CLAUDE.md: n8n-report-automation

## Purpose
A small automation that reads sales data from a CSV file, computes a daily summary, and sends it to a Telegram chat on a schedule. Built as an n8n workflow with a small Python helper for the calculation. Portfolio demo project, not client work.

## Stack
- n8n (self-hosted, Docker Compose, free)
- Python 3.12, uv, pytest, ruff, mypy for the helper script
- No paid services. Telegram bot token and a test CSV only.

## Structure
- `workflows/daily_report.json`: exported n8n workflow
- `src/report/`: pure functions that compute the summary from rows (no I/O)
- `src/report/cli.py`: reads a CSV path and prints the summary as JSON
- `data/sample_sales.csv`: synthetic data only
- `tests/`: unit tests for the summary functions
- `docs/TZ.md`, `docs/TASKS.md`, `docs/OPEN-QUESTIONS.md`

## Rules
- Never commit a Telegram token, n8n credentials, or real sales data. Use `.env.example` for variable names only.
- Money values are integers in minor units (cents). No floats for amounts.
- The helper must not import n8n or Telegram code. Keep it pure.
- Tests use `data/sample_sales.csv` or inline synthetic rows.
- Code identifiers, file names, and commit messages in English.

## Workflow
- Work only on the task the tech lead assigned in `docs/TASKS.md`.
- One task per branch named `task/<id>-<slug>`, one commit per logical step.
- Before reporting a task done: `uv run ruff check .`, `uv run mypy src`, `uv run pytest` must pass.
- Do not push to `main`. Push task branches and the `integration` branch only.

## Stop and write a question in `docs/OPEN-QUESTIONS.md` instead of deciding, if
- a task needs a choice listed in OPEN-QUESTIONS.md;
- a new dependency is needed;
- a change would alter the workflow's trigger time or Telegram chat;
- a test fails and the fix is unclear after two attempts.
