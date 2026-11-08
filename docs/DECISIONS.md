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

### T5: n8n workflow export (done)
- Done: `workflows/daily_report.json` (Manual Trigger -> Read CSV -> Run Report CLI -> Format Message -> Send Telegram), placeholders only, manual trigger only (no schedule: Q1 is the owner's). `docs/OPEN-QUESTIONS.md` has a section listing the values the owner must set (send time/time zone, chat id, credential).
- Coverage: criterion 1 by `test_valid_json_with_nodes_and_connections`, `test_manual_trigger_only`, `test_chain_ends_in_telegram_and_runs_cli`; 2 by `test_no_token_shaped_string`, `test_chat_id_and_credentials_are_placeholders`; 3 by inspection of OPEN-QUESTIONS.md. Tester green (17 tests).
- Risks: NOT verified in a real n8n instance (structure only; node typeVersions unconfirmed). Read CSV node is redundant (CLI reads the file itself). Execute Command needs `uv` and the repo in the n8n container and may be disabled by default in recent n8n (`NODES_EXCLUDE`); no docker-compose yet. Format Message code node uses `/100` + `toFixed(2)` for display, a float step in the workflow (CLAUDE.md bans floats for amounts; Python helper is clean). Q4 (no-orders display) not handled. Sample data gives identical totals on all 3 dates.

## Session 2
- T5 status changed to blocked: `.env` values for Telegram are empty (owner fills them manually). The workflow file itself stays as accepted; only a live send is blocked.

### T6: Integer money formatting in workflow (done)
- Done: Format Message node now uses `abs % 100` and `(abs - rem) / 100` with zero-padded remainder; negatives get a leading "-". No `toFixed`.
- Coverage: criterion 1 by `test_format_message_has_no_float_money`; 2 by `test_format_message_formats_cents_with_node` (runs node; ran, not skipped; also -5 and -17183); 3 by the remaining tests. Tester green (19 tests) plus manual node checks (99, 101, 999999, large values).
- Risks: the node test skips if `node` is not installed; no thousands separators; still not imported into a real n8n.

## T7 decision: how the Execute Command node runs the helper

- **Decision:** call the helper without uv: `PYTHONPATH=/app/src python3 -m report.cli /data/sample_sales.csv`. The n8n image used by T9 must therefore contain `python3` (a small custom image on top of `n8nio/n8n`), the repo's `src/` mounted at `/app/src` and the data directory mounted at `/data`. No uv, no pyproject, no virtualenv in the container.
- **Reason:** the helper is stdlib-only (`argparse`, `csv`, `json`, `sys`, `collections`, `dataclasses`), so uv adds nothing at runtime. Installing uv in the image is one more moving part. Absolute paths on both `PYTHONPATH` and the CSV make the command independent of the working directory (n8n's cwd for Execute Command is not controlled by us). A test runs the command from an unrelated directory.
- **Execute Command is disabled by default in n8n 2.x** (n8n docs, "2.0 breaking changes": "Disable ExecuteCommand and LocalFileTrigger nodes by default"). To enable it, set `NODES_EXCLUDE: "[]"` for the n8n container (docs: "To enable all nodes, specify `NODES_EXCLUDE: "[]"`"). T9 must set this in docker-compose.
- **Requirements handed to T9:** (1) custom image with `python3` (project targets 3.12; the helper uses nothing version-specific beyond what 3.12 provides, but Alpine's packaged python3 version should be checked); (2) volumes `./src:/app/src:ro` and `./data:/data:ro`; (3) `NODES_EXCLUDE=[]`.
- **Not verified:** no Docker or n8n instance was run here. Not confirmed: the python3 version available via apk for the current n8n image, whether the current n8nio/n8n image still ships `apk` for installing it (may require a build stage), and that the node runs the command through a shell (needed for the `PYTHONPATH=...` prefix; the test assumes `sh -c`).

### T7: Execute Command requirements (done)
- Done: Run Report CLI node now runs `PYTHONPATH=/app/src python3 -m report.cli /data/sample_sales.csv` (no uv, absolute paths); decision and reasons are in the 'T7 decision' section above. Tech lead fixed a stale 'needs uv' line in OPEN-QUESTIONS.md found by the tester.
- Coverage: criterion 1 by inspection of the T7 decision section; 2 by `test_command_matches_t7_decision`, `test_command_has_no_uv_cwd_dependence_or_placeholder`, `test_command_runs_from_any_directory`. Tester green (22 tests).
- Risks (unverified, no Docker/n8n here): python3 availability/version in the n8n image (needs custom image, T9); that Execute Command uses a shell (needed for the `PYTHONPATH=` prefix); `NODES_EXCLUDE=[]` effect; the local test rewrites /app/src and /data, so it does not prove the container layout.

### T8: Sample data and malformed rows (done)
- Root cause: data issue. The CSV was 9 identical rows repeated for each of the 3 dates, so identical summaries were correct behaviour. Fixed by rewriting `data/sample_sales.csv` to 22 rows with per-day differences (now 11488 / 15244 / 17097 cents). `report.cli` now reports a short row as `error: cannot read <path>: line N: missing field(s): <names>` with exit 1 and no traceback.
- Coverage: criterion 1 by `test_sample_dates_give_different_summaries` (T2 tests still pass); 2 by `test_short_row_reports_line_and_fails`. Tester green (21 tests on the branch; also green after merge with T7).
- Risks: empty or header-only CSV prints `[]` with exit 0 (n8n would send an empty report); rows with extra fields are silently accepted; wrong header gives terse message (`'date'`); non-integer errors have no line number.
