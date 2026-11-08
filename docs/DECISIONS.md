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
- Risks: NOT verified in a real n8n instance (structure only; node typeVersions unconfirmed). Read CSV node is redundant (CLI reads the file itself). Execute Command needs `uv` and the repo in the n8n container and may be disabled by default in recent n8n (`NODES_EXCLUDE`); no docker-compose yet. Format Message code node uses `/100` + `toFixed(2)` for display, a float step in the workflow (project rules ban floats for amounts; Python helper is clean). Q4 (no-orders display) not handled. Sample data gives identical totals on all 3 dates.

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

### T9: docker-compose for n8n (done, with an unverified build)
- Done: `Dockerfile` (n8n image + `apk add python3`, back to `USER node`), `docker-compose.yml` (mounts `./src:/app/src:ro`, `./data:/data:ro`, `./n8n_data`; `NODES_EXCLUDE=[]`; Telegram and timezone variables only as `${VAR}` references, no defaults), `.env.example` names, `docs/RUN.md`, `tests/test_compose.py`.
- Coverage: criterion 1 by `test_compose_is_well_formed_text`, `test_no_secret_shaped_strings`, `test_docker_compose_config` (real `docker compose config`, ran); 2 by `test_variables_are_references_only`, `test_env_example_has_names_with_empty_values`, `test_no_default_time_or_timezone`. Tester: all T9 criteria covered, 31 tests green.
- Tester verdict was formally FAIL only because the optional `docker build` check could not run (Docker daemon not running). Tech lead accepted because both acceptance criteria are verified; the build is NOT verified.
- Risks: `apk add python3` on `n8nio/n8n:latest` and its python3 version unverified; `:latest` unpinned; `./n8n_data` may be root-owned (container runs as uid 1000); empty `TZ`/`GENERIC_TIMEZONE` reach the container as empty strings; `TELEGRAM_*` are passed to the container but the workflow does not read them yet; `REPORT_CSV_PATH` is unused.

## Session 3: decisions by the owner
- **Q1 (send time):** 09:00 every day, time zone Europe/Chisinau. Decided by the owner. Applied in T10.
- **Q2 (chat id):** the owner put it in `.env`; it is never committed. Q6 is closed the same way (token and chat id set by the owner in `.env`; agents do not read or print the values).
- **Q4 (date without orders):** show the line `no sales`. Decided by the owner. Applied in T11.
- **Q8:** the owner performs the manual Docker/n8n verification; agents do what they can and write exact steps.

### T9 (re-verified, accepted): Dockerfile build and run
- Problem found: `docker.n8n.io` rate-limited (429); the Docker Hub image `n8nio/n8n` (2.46.6) is a Docker Hardened Image with no `apk` and no python3, so the earlier `apk add python3` Dockerfile could not work.
- Fix: multi-stage Dockerfile, `FROM python:3.12-alpine AS python` + `FROM n8nio/n8n:2.46.6` + `COPY --from=python /usr/local /usr/local` + `USER node`. Both images are musl-based; python3 needs only libpython and musl for the stdlib modules the helper uses.
- Verified by tester (PASS): `docker build -t t9-check .` ok (cached layers; developer's own build was cold), `python3 --version` -> 3.12.16, literal `sh -c 'PYTHONPATH=/app/src python3 -m report.cli /data/sample_sales.csv'` in the container prints the JSON, rc 0; `docker compose config` ok; 32 tests green.
- Risks: tester's build used cached layers; `python:3.12-alpine` tag floats within 3.12; only tested on aarch64; `./n8n_data` ownership vs uid 1000 untested; n8n itself was not started.

### T10: Env-driven workflow and schedule (done)
- Done: Manual Trigger kept; Schedule Trigger added (cron `0 9 * * *`, `settings.timezone` = `Europe/Chisinau`, owner decision Q1). Telegram node replaced by an HTTP Request node posting to `https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendMessage` with `chat_id` from `$env.TELEGRAM_CHAT_ID`; no n8n credential needed. CSV path from `$env.REPORT_CSV_PATH` with the non-secret fallback `/data/sample_sales.csv` (the owner's `REPORT_CSV_PATH` is empty). Redundant Read CSV node removed. Compose sets `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` and passes the variables as `${VAR}` references only.
- Coverage: tests in `tests/test_workflow.py` (env variables via `$env`, cron and timezone, manual trigger kept, both triggers feed the chain, no token or chat-id-shaped values) and `tests/test_compose.py` (references only, env access flag). Tester PASS, 37 tests green after merge.
- Risks: the token is in the request URL, so it can appear in n8n execution data in `./n8n_data` and in the UI (owner can set `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none` and `EXECUTIONS_DATA_SAVE_ON_ERROR=none`; revoke the token if exposed); `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` exposes all container env vars to every node (acceptable for a single-user local demo); the workflow is exported with `active: false`, so the schedule runs only after activation; empty `REPORT_CSV_PATH` silently falls back to the sample file; import into n8n, scheduleTrigger 1.2 loading and the 09:00 firing in Europe/Chisinau are unverified.

### T11: "no sales" line (done)
- Done: `src/report/dates.py` (pure `parse_date`, `date_range`); `report.cli` gets optional `--from` / `--to` (default range = min..max of the CSV dates, so gaps get entries with 0 revenue, 0 orders, null top product); invalid dates exit 2 with an `error:` message; Format Message node prints `<date>: no sales` when `orders === 0`, integer-only money kept.
- Coverage: `test_gap_date_inside_range_has_zero_entry`, `test_date_with_orders_unchanged`, `test_from_to_extend_range`, `test_invalid_date_args`, `test_empty_file_still_empty_list` (tests/test_cli.py); `test_format_message_no_sales_line` (node). Tester PASS, 46 tests green.
- Risks: the workflow command passes no `--from/--to`, so only gaps inside the CSV's own date range show "no sales"; a "yesterday with no data" case needs `--from/--to` expressions in the command (not done, changes the command; owner or a later task). A CSV date not in strict YYYY-MM-DD now fails (exit 2). A very wide range gives one line per day and could exceed Telegram's 4096-character limit (no guard). `date_range` has no direct unit tests, only CLI-level ones.

### T12: n8n compatibility check (done; owner steps remain)
- Done: n8n 2.46.6 was run in Docker Compose with a throwaway env file (fake values, real `.env` not used) by the developer and again independently by the tester: image builds, `n8n import:workflow` succeeds, `list:workflow` shows 'Daily sales report', `n8n execute` from the Manual Trigger runs Run Report CLI (exit 0, uid 1000, python3 3.12.16) and Format Message, and Send Telegram reaches api.telegram.org and fails 404 only because the token was fake. The published workflow starts the scheduler without errors. No code fixes were needed. `docs/RUN.md` has an 'Owner checklist' (4 steps).
- Coverage: tester PASS; `tests/test_run_doc.py::test_owner_checklist_section`; 47 tests green.
- Not verified (owner): import through the n8n UI; the cron firing at 09:00 Europe/Chisinau; a real Telegram send with the real token and chat id; only aarch64 tested. The token is stored in n8n execution data because it is in the request URL (confirmed in the run); optional `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none` and `EXECUTIONS_DATA_SAVE_ON_ERROR=none`.

- T5 unblocked: the owner filled `.env` (Q2, Q6). The real Telegram send remains the owner's manual check (Q8).

## Session 4
### T13: --from/--to in the workflow command (done)
- Done: Run Report CLI appends `--from '<REPORT_FROM>'` / `--to '<REPORT_TO>'` only when the variable is non-empty; single quotes are stripped from the values. `REPORT_FROM`/`REPORT_TO` added to compose (as `${VAR}` references) and `.env.example` (empty). CLI and `dates.py` needed no change: dates outside the range are already not printed.
- Coverage: `test_from_to_print_only_dates_inside_range` (CLI), `test_range_variables_add_flags_and_filter_dates`, `test_in_range_gap_date_prints_no_sales`, `test_empty_or_unset_range_keeps_whole_file`, `test_only_one_bound_set`, `test_single_quotes_stripped_from_range_values`, `test_invalid_range_rejected_by_cli_not_n8n`, JSON/secret tests. Tester PASS (56 tests on the branch) including a real n8n 2.46.6 run with fake values: range set -> only 2025-01-02..03; empty -> all three dates; a quote-injection value was not executed as shell and the CLI rejected it (fails closed).
- Risks: cron firing and a real Telegram send are still unverified; whitespace-only values count as non-empty and are rejected by the CLI (exit 2); an invalid date makes the workflow fail and send nothing; after changing `.env` the container must be recreated (`docker compose up -d`); the tester's build used the image tag `n8n-report-automation:local` and removed it afterwards, so the owner should rebuild with `docker compose build`.

### T14: n8n execution data settings (done)
- Done: `EXECUTIONS_DATA_SAVE_ON_SUCCESS: "none"` and `EXECUTIONS_DATA_SAVE_ON_ERROR: "none"` in docker-compose.yml with a comment (token is in the request URL); names and values checked against the n8n 2.46.6 image config (valid, not deprecated, default `all`); 'Execution data settings' section in docs/RUN.md (effect and undo). Tech lead removed the stale 'Optional' paragraph and the 'look at Executions' hint that contradicted the new setting (found by the tester).
- Coverage: `test_docker_compose_config`, `test_execution_data_is_not_saved`, `test_run_docs_explain_execution_data_settings`. Tester PASS (49 tests on the branch).
- Risks: with storage off, past runs cannot be inspected in the UI (debugging is harder); the token is still visible in live manual-run output; takes effect only after the container is recreated.

Full checks after merging T13 and T14 into integration: `ruff check .` ok, `mypy src` ok, `pytest` 58 passed, `docker compose --env-file /dev/null config --quiet` rc 0.

### T15: Repository cleanup (done)
- Done: all service worktrees (agent worktrees and scratchpad ones) removed with `git worktree remove`; local branch `task/T8-data-malformed` deleted. `git worktree list` shows only the main working copy; `git status` is clean.
- Verified by tester (PASS): worktree list, branch absent, clean status; final checks on integration: ruff ok, mypy ok, 58 tests passed, `docker compose config` rc 0 with the execution-data and REPORT_FROM/REPORT_TO variables; local integration == origin/integration; origin/main unchanged (`b66b591`); `.env` untracked and ignored; no token-shaped strings or chat ids in tracked files.
- Left on purpose: local branches `worktree-agent-*` and `task/T8-data-malformed-wt` (created by agent worktrees; their content is on the pushed task branches). The owner can delete them with `git branch -D`.
