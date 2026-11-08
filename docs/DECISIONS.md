# Decisions

## Open-question decisions (tech lead)

- **D1 (Q3, CSV source):** local folder. Reason: this is the stated default proposal; no network dependency, matches the Docker volume setup and the CLI taking a path.
- **D2 (Q5, top product):** by revenue. Reason: default proposal; matches T3 acceptance criteria (top product by revenue).

Q1 (send time/time zone), Q2 (Telegram chat id) and Q4 (no-orders display) have no default proposal and stay with the owner.

## Accepted tasks

### T1: Project skeleton (done)
- Done: pyproject.toml (hatchling build backend, pytest/ruff/mypy dev group, mypy strict), uv.lock, .python-version, .gitignore, .env.example (names only), src/report/__init__.py, smoke test.
- Coverage: criterion 1 by `uv sync` (command check); 2 by `tests/test_smoke.py::test_package_imports`; 3 by `ruff check .` and `mypy src`. Tester reported all green.
- Risks: hatchling choice and `.env.example` variable names were the developer's picks (T5 may adjust names). `.gitignore` also ignores `.idea/` and `n8n_data/`.

### T2: Sample data (done)
- Done: `data/sample_sales.csv` (27 synthetic rows, 3 dates 2025-01-01..03, 3 products widget/gadget/gizmo, integer cents) and `tests/test_sample_data.py`.
- Coverage: criterion 1 by `test_header_and_row_count`; criterion 2 by `test_unit_price_cents_non_negative_integers`; extra `test_covers_three_days_and_three_products`. Tester green (4 tests).
- Risks: price check uses `str.isdigit()` (accepts exotic Unicode digits, harmless for this file).

### T3: Daily summary function (done)
- Done: `src/report/summary.py` with `SaleRow`, `DailySummary`, pure `summarize(rows)`; revenue aggregated per product, top product by key (-revenue, name).
- Coverage: criterion 1 by `test_revenue_is_integer_quantity_times_price`; 2 by `test_empty_input`; 3 by `test_tie_resolved_by_name_ascending`; plus per-product aggregation and sample-data smoke tests. Tester green (9 tests).
- Risks: `orders` = number of input rows (CSV has no order id); no date check or validation of negative/zero quantities; `SaleRow` type was the developer's addition.

### T4: CLI (done)
- Done: `src/report/cli.py` (`main(argv) -> int`, stdlib only). Output is a JSON array sorted by date: `{date, total_revenue_cents, orders, top_product}`. Missing file: `error: file not found: <path>` on stderr, exit 2; unreadable file / bad column / non-integer value: exit 1.
- Coverage: criterion 1 by `test_module_prints_valid_json`; 2 by `test_one_entry_per_date_sorted`; 3 by `test_missing_file`. Tester green (12 tests) plus manual CLI checks.
- Risks: a CSV row with a missing field raises an uncaught `TypeError` traceback (exit 1) instead of the clean error (tester finding, outside acceptance criteria; candidate follow-up). Empty CSV prints `[]` with exit 0. Dates without orders never appear in output (relates to open Q4, owner's decision).
