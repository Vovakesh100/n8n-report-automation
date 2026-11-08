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
- Status: done
- Depends on: T1
- Do: create `data/sample_sales.csv` with synthetic rows: `date,product,quantity,unit_price_cents`, at least 20 rows across 3 days and 3 products.
- Acceptance:
  1. The file has a header and at least 20 data rows.
  2. A test reads the file and checks that every `unit_price_cents` is a non-negative integer.

## T3: Daily summary function
- Status: done
- Depends on: T2
- Do: in `src/report/summary.py`, write a pure function that takes rows for one date and returns total revenue in cents, count of orders, and the top product by revenue.
- Acceptance:
  1. Revenue is computed as `quantity * unit_price_cents` and stays an integer.
  2. Empty input returns zero revenue, zero orders, and no top product.
  3. A tie for top product is resolved by the product name in ascending order, and a test checks it.

## T4: CLI
- Status: done
- Depends on: T3
- Do: in `src/report/cli.py`, read a CSV path from the command line, group rows by date, and print one JSON summary per date.
- Acceptance:
  1. `uv run python -m report.cli data/sample_sales.csv` prints valid JSON.
  2. The output has one entry per date in the file.
  3. A missing file produces a clear error message and a non-zero exit code.

## T5: n8n workflow export
- Status: blocked (workflow file accepted; real Telegram send blocked until the owner fills .env, see OPEN-QUESTIONS.md Q6)
- Depends on: T4
- Do: create `workflows/daily_report.json` for a manually triggered workflow that reads the CSV, runs the summary, and sends the result to a Telegram node. Use placeholder credential names only.
- Acceptance:
  1. The JSON is valid and loads in n8n.
  2. The workflow has no real token or chat id; they are placeholders.
  3. `docs/OPEN-QUESTIONS.md` lists the schedule time and chat id the owner must set.

## T6: Integer money formatting in workflow
- Status: done
- Depends on: T5
- Do: replace `/100` + `toFixed(2)` in the Format Message node with integer division and remainder.
- Acceptance:
  1. The node code has no `toFixed` or float division for amounts.
  2. A test runs the node code (via node, skipped if absent) for 0, 5, 100, 17183, 100000.
  3. Existing tests pass.

## T7: Execute Command requirements
- Status: todo
- Depends on: T6
- Do: determine what the n8n Execute Command node needs (uv in the container, or a call without uv); document the decision and fix the workflow.
- Acceptance:
  1. The decision and its reason are in `docs/DECISIONS.md`.
  2. The workflow command matches the decision; a test checks it.

## T8: Sample data and malformed rows
- Status: todo
- Depends on: T6
- Do: find out why all three dates give identical summaries; fix the data or document the cause. Handle an incomplete CSV row with a clear message and non-zero exit.
- Acceptance:
  1. Dates in the sample data give different results, or the cause is documented.
  2. A test covers a short CSV row: clear stderr message, non-zero exit.

## T9: docker-compose for n8n
- Status: todo
- Depends on: T7
- Do: add `docker-compose.yml` with n8n for local runs, variables from `.env`, no real keys.
- Acceptance:
  1. The file is valid YAML and contains no secrets.
  2. Variables come from `.env` / `.env.example`.
