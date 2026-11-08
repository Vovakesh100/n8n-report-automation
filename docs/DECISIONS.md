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
