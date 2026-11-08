# Tasks

Status values: `todo`, `in-progress`, `blocked`, `done`.

## T1: Project skeleton
- Status: done
- Depends on: none
- Do: create `pyproject.toml` (Python 3.12, uv, ruff, mypy, pytest), `src/report/__init__.py`, `tests/`, `.gitignore`, `.env.example` with variable names only.
- Acceptance:
  1. `uv sync` completes without errors.
  2. `uv run pytest` runs and passes one smoke test.
  3. `uv run ruff check .` and `uv run mypy src` pass.

## T2: Sample data
- Status: todo
- Depends on: T1
- Do: create `data/sample_sales.csv` with synthetic rows: `date,product,quantity,unit_price_cents`, at least 20 rows across 3 days and 3 products.
- Acceptance:
  1. The file has a header and at least 20 data rows.
  2. A test reads the file and checks that every `unit_price_cents` is a non-negative integer.

## T3: Daily summary function
- Status: todo
- Depends on: T2
- Do: in `src/report/summary.py`, write a pure function that takes rows for one date and returns total revenue in cents, count of orders, and the top product by revenue.
- Acceptance:
  1. Revenue is computed as `quantity * unit_price_cents` and stays an integer.
  2. Empty input returns zero revenue, zero orders, and no top product.
  3. A tie for top product is resolved by the product name in ascending order, and a test checks it.

## T4: CLI
- Status: todo
- Depends on: T3
- Do: in `src/report/cli.py`, read a CSV path from the command line, group rows by date, and print one JSON summary per date.
- Acceptance:
  1. `uv run python -m report.cli data/sample_sales.csv` prints valid JSON.
  2. The output has one entry per date in the file.
  3. A missing file produces a clear error message and a non-zero exit code.

## T5: n8n workflow export
- Status: todo
- Depends on: T4
- Do: create `workflows/daily_report.json` for a manually triggered workflow that reads the CSV, runs the summary, and sends the result to a Telegram node. Use placeholder credential names only.
- Acceptance:
  1. The JSON is valid and loads in n8n.
  2. The workflow has no real token or chat id; they are placeholders.
  3. `docs/OPEN-QUESTIONS.md` lists the schedule time and chat id the owner must set.
