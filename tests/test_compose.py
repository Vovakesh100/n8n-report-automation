"""Text-based checks for docker-compose.yml (no YAML dependency)."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = (ROOT / "docker-compose.yml").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()
NAMES = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "REPORT_CSV_PATH", "REPORT_FROM", "REPORT_TO", "GENERIC_TIMEZONE", "TZ"]


def test_compose_is_well_formed_text() -> None:
    assert "\t" not in COMPOSE
    assert COMPOSE.startswith("services:")
    assert re.search(r"^  n8n:$", COMPOSE, re.MULTILINE)


def test_no_secret_shaped_strings() -> None:
    assert not re.search(r"\d{6,}:[A-Za-z0-9_-]{20,}", COMPOSE)  # Telegram token shape
    assert not re.search(r"(?i)(token|secret|password|key)\s*[:=]\s*[\"']?[A-Za-z0-9]{8,}", COMPOSE)


def test_variables_are_references_only() -> None:
    for name in NAMES:
        assert re.search(rf"^\s+{name}: \$\{{{name}\}}$", COMPOSE, re.MULTILINE), name


def test_no_default_time_or_timezone() -> None:
    assert not re.search(r"\$\{(GENERIC_TIMEZONE|TZ):-", COMPOSE)
    assert not re.search(r"(?i)\b(Europe|America|Asia|UTC)\b", COMPOSE)


def test_t7_requirements() -> None:
    assert 'NODES_EXCLUDE: "[]"' in COMPOSE
    assert "./src:/app/src:ro" in COMPOSE
    assert "./data:/data:ro" in COMPOSE
    assert "./n8n_data:" in COMPOSE
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert dockerfile.rstrip().endswith("USER node")


def test_dockerfile_pins_versions_and_has_no_apk() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    code = [ln for ln in dockerfile.splitlines() if not ln.lstrip().startswith("#")]
    assert not any("apk add" in ln for ln in code)
    froms = [ln.split()[1] for ln in code if ln.startswith("FROM ")]
    assert len(froms) == 2
    for image in froms:
        assert ":" in image and not image.endswith(":latest"), image
    n8n = [i for i in froms if "n8nio/n8n" in i]
    assert n8n and re.fullmatch(r"n8nio/n8n:\d+\.\d+\.\d+", n8n[0]), n8n
    assert not any("docker.n8n.io" in ln for ln in code)
    assert "COPY --from=" in dockerfile and "/usr/local" in dockerfile


def test_env_example_has_names_with_empty_values() -> None:
    values = dict(line.split("=", 1) for line in ENV_EXAMPLE.splitlines() if "=" in line)
    for name in NAMES:
        assert values.get(name) == ""


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_docker_compose_config(tmp_path: Path) -> None:
    env = tmp_path / "empty.env"
    env.write_text("")
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(env), "config", "--quiet"],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if "daemon" in result.stderr.lower() and result.returncode != 0:
        pytest.skip("docker compose unavailable: " + result.stderr[:100])
    assert result.returncode == 0, result.stderr


def test_env_access_in_nodes_is_enabled() -> None:
    assert 'N8N_BLOCK_ENV_ACCESS_IN_NODE: "false"' in COMPOSE


def test_execution_data_is_not_saved() -> None:
    for name in ("EXECUTIONS_DATA_SAVE_ON_SUCCESS", "EXECUTIONS_DATA_SAVE_ON_ERROR"):
        assert re.search(rf'^      {name}: "none"$', COMPOSE, re.MULTILINE), name


def test_run_docs_explain_execution_data_settings() -> None:
    docs = (ROOT / "docs" / "RUN.md").read_text()
    section = docs.split("## Execution data settings", 1)[1]
    assert "EXECUTIONS_DATA_SAVE_ON_SUCCESS" in section
    assert "EXECUTIONS_DATA_SAVE_ON_ERROR" in section
    assert "Undo" in section and "`all`" in section and "docker compose up -d" in section
