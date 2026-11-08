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
