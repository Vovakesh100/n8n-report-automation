import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "workflows" / "daily_report.json"


def load() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    return data


def _nodes() -> dict[str, dict[str, Any]]:
    return {n["name"]: n for n in load()["nodes"]}


def test_valid_json_with_nodes_and_connections() -> None:
    wf = load()
    assert wf["nodes"]
    assert wf["connections"]
    names = {n["name"] for n in wf["nodes"]}
    for src, conn in wf["connections"].items():
        assert src in names
        for branch in conn["main"]:
            for target in branch:
                assert target["node"] in names


def test_manual_trigger_still_present() -> None:
    assert "n8n-nodes-base.manualTrigger" in [n["type"] for n in load()["nodes"]]


def test_schedule_trigger_cron_and_timezone() -> None:
    wf = load()
    schedule = _nodes()["Schedule Trigger"]
    assert schedule["type"] == "n8n-nodes-base.scheduleTrigger"
    assert schedule["parameters"]["rule"]["interval"] == [{"field": "cronExpression", "expression": "0 9 * * *"}]
    assert wf["settings"]["timezone"] == "Europe/Chisinau"


def test_both_triggers_feed_the_same_chain() -> None:
    conns = load()["connections"]
    for trigger in ("Manual Trigger", "Schedule Trigger"):
        assert conns[trigger]["main"] == [[{"node": "Run Report CLI", "type": "main", "index": 0}]]


def test_chain_ends_in_telegram_http_request_and_runs_cli() -> None:
    nodes = _nodes()
    assert nodes["Send Telegram"]["type"] == "n8n-nodes-base.httpRequest"
    assert "report.cli" in nodes["Run Report CLI"]["parameters"]["command"]
    conns = load()["connections"]
    assert conns["Run Report CLI"]["main"][0][0]["node"] == "Format Message"
    assert conns["Format Message"]["main"][0][0]["node"] == "Send Telegram"


def test_no_token_or_chat_id_shaped_values() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert not re.search(r"\d{6,}:[A-Za-z0-9_-]{30,}", text)  # bot token shape
    assert not re.search(r"(?<![\w.-])-?\d{8,}(?![\w.-])", text)  # chat id shape
    assert "credentials" not in text
    assert "REPLACE_WITH" not in text


def test_telegram_request_reads_env_variables() -> None:
    params = _nodes()["Send Telegram"]["parameters"]
    assert params["method"] == "POST"
    assert params["url"] == "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendMessage"
    body = {p["name"]: p["value"] for p in params["bodyParameters"]["parameters"]}
    assert body["chat_id"] == "={{ $env.TELEGRAM_CHAT_ID }}"
    assert body["text"] == "={{ $json.text }}"


def test_all_three_env_variables_referenced_via_env() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "REPORT_CSV_PATH"):
        assert f"$env.{name}" in text


def _format_code() -> str:
    code: str = _nodes()["Format Message"]["parameters"]["jsCode"]
    return code


def test_format_message_has_no_float_money() -> None:
    code = _format_code()
    assert "toFixed" not in code
    assert not re.search(r"cents\s*/\s*100", code)


def test_format_message_formats_cents_with_node(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    cases = {0: "0.00", 5: "0.05", 100: "1.00", 17183: "171.83", 100000: "1000.00", -5: "-0.05", -17183: "-171.83"}
    harness = (
        "const code = process.argv[2];\n"
        "const fn = new Function('$input', code);\n"
        "const out = {};\n"
        "for (const c of JSON.parse(process.argv[3])) {\n"
        "  const stdout = JSON.stringify([{date: 'D', total_revenue_cents: c, orders: 1, top_product: 'P'}]);\n"
        "  out[c] = fn({first: () => ({json: {stdout}})})[0].json.text;\n"
        "}\n"
        "console.log(JSON.stringify(out));\n"
    )
    script = tmp_path / "harness.js"
    script.write_text(harness, encoding="utf-8")
    result = subprocess.run(
        [node, str(script), _format_code(), json.dumps(list(cases))],
        capture_output=True,
        text=True,
        check=True,
    )
    texts = json.loads(result.stdout)
    for cents, expected in cases.items():
        assert f"revenue {expected}," in texts[str(cents)]


def test_format_message_no_sales_line(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    harness = (
        "const fn = new Function('$input', process.argv[2]);\n"
        "const stdout = process.argv[3];\n"
        "console.log(fn({first: () => ({json: {stdout}})})[0].json.text);\n"
    )
    script = tmp_path / "harness2.js"
    script.write_text(harness, encoding="utf-8")
    entries = [
        {"date": "2025-01-01", "total_revenue_cents": 17183, "orders": 2, "top_product": "Widget"},
        {"date": "2025-01-02", "total_revenue_cents": 0, "orders": 0, "top_product": None},
    ]
    result = subprocess.run(
        [node, str(script), _format_code(), json.dumps(entries)],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert "2025-01-02: no sales" in lines
    assert "2025-01-01: revenue 171.83, orders 2, top product Widget" in lines


EXPRESSION = "{{ $env.REPORT_CSV_PATH || '/data/sample_sales.csv' }}"
EXPECTED_COMMAND = f"=PYTHONPATH=/app/src python3 -m report.cli '{EXPRESSION}'"


def _command() -> str:
    node = _nodes()["Run Report CLI"]
    assert node["type"] == "n8n-nodes-base.executeCommand"
    command: str = node["parameters"]["command"]
    return command


def test_command_matches_t7_form_with_env_csv_path() -> None:
    assert _command() == EXPECTED_COMMAND


def test_command_has_no_uv_cwd_dependence_or_placeholder() -> None:
    command = _command()
    assert "uv" not in command.split()
    assert "REPLACE" not in command
    assert "PYTHONPATH=/app/src " in command  # absolute source dir, not relative to the cwd
    assert f"'{EXPRESSION}'" in command  # path is single-quoted for the shell
    assert "'/data/sample_sales.csv'" in EXPRESSION  # non-secret default when the variable is empty


@pytest.mark.parametrize("env_value", ["", str(ROOT / "data" / "sample_sales.csv")])
def test_command_runs_from_any_directory(tmp_path: Path, env_value: str) -> None:
    # Emulate the n8n expression: the env value, or the default path when it is empty.
    path = env_value or str(ROOT / "data" / "sample_sales.csv")
    command = _command().removeprefix("=").replace(EXPRESSION, path).replace("/app/src", str(ROOT / "src"))
    result = subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True, text=True, check=True)
    assert isinstance(json.loads(result.stdout), list)
