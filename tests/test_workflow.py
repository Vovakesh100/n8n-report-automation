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


CSV_EXPRESSION = "{{ $env.REPORT_CSV_PATH || '/data/sample_sales.csv' }}"
FROM_EXPRESSION = "{{ $env.REPORT_FROM ? \" --from '\" + String($env.REPORT_FROM).replace(/'/g, '') + \"'\" : '' }}"
TO_EXPRESSION = "{{ $env.REPORT_TO ? \" --to '\" + String($env.REPORT_TO).replace(/'/g, '') + \"'\" : '' }}"
EXPECTED_COMMAND = (
    f"=PYTHONPATH=/app/src python3 -m report.cli '{CSV_EXPRESSION}'{FROM_EXPRESSION}{TO_EXPRESSION}"
)
SAMPLE = ROOT / "data" / "sample_sales.csv"


def _command() -> str:
    node = _nodes()["Run Report CLI"]
    assert node["type"] == "n8n-nodes-base.executeCommand"
    command: str = node["parameters"]["command"]
    return command


def _render(tmp_path: Path, env: dict[str, str]) -> str:
    """Evaluate the {{ }} expressions of the command with node, like n8n does for $env."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    harness = (
        "const env = JSON.parse(process.argv[3]);\n"
        "const t = process.argv[2].replace(/^=/, '');\n"
        "const out = t.replace(/\\{\\{(.*?)\\}\\}/g, (m, e) => String(new Function('$env', 'return (' + e + ')')(env)));\n"
        "process.stdout.write(out);\n"
    )
    script = tmp_path / "render.js"
    script.write_text(harness, encoding="utf-8")
    result = subprocess.run(
        [node, str(script), _command(), json.dumps(env)], capture_output=True, text=True, check=True
    )
    return result.stdout


def _run(tmp_path: Path, env: dict[str, str], csv_path: Path = SAMPLE) -> Any:
    env = {"REPORT_CSV_PATH": str(csv_path), **env}
    command = _render(tmp_path, env).replace("/app/src", str(ROOT / "src"))
    result = subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_command_matches_t7_form_with_env_csv_path_and_range() -> None:
    assert _command() == EXPECTED_COMMAND


def test_command_has_no_uv_cwd_dependence_or_placeholder() -> None:
    command = _command()
    assert "uv" not in command.split()
    assert "REPLACE" not in command
    assert "PYTHONPATH=/app/src " in command  # absolute source dir, not relative to the cwd
    assert f"'{CSV_EXPRESSION}'" in command  # path is single-quoted for the shell
    assert "'/data/sample_sales.csv'" in CSV_EXPRESSION  # non-secret default when the variable is empty


def test_env_range_variables_referenced_via_env() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "$env.REPORT_FROM" in text and "$env.REPORT_TO" in text


@pytest.mark.parametrize("env_value", ["", str(SAMPLE)])
def test_command_runs_from_any_directory(tmp_path: Path, env_value: str) -> None:
    env = {"REPORT_CSV_PATH": env_value}
    command = _render(tmp_path, env).replace("/app/src", str(ROOT / "src"))
    if not env_value:
        command = command.replace("/data/sample_sales.csv", str(SAMPLE))
    result = subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True, text=True, check=True)
    assert isinstance(json.loads(result.stdout), list)


@pytest.mark.parametrize("env", [{}, {"REPORT_FROM": "", "REPORT_TO": ""}])
def test_empty_or_unset_range_keeps_whole_file(tmp_path: Path, env: dict[str, str]) -> None:
    rendered = _render(tmp_path, {"REPORT_CSV_PATH": "/x.csv", **env})
    assert "--from" not in rendered and "--to" not in rendered
    assert rendered == "PYTHONPATH=/app/src python3 -m report.cli '/x.csv'"
    dates = sorted({ln.split(",")[0] for ln in SAMPLE.read_text().splitlines()[1:] if ln})
    assert [e["date"] for e in _run(tmp_path, env)] == dates


def test_range_variables_add_flags_and_filter_dates(tmp_path: Path) -> None:
    csv_path = tmp_path / "s.csv"
    csv_path.write_text(
        "date,product,quantity,unit_price_cents\n"
        "2025-01-01,Widget,1,100\n"
        "2025-01-03,Widget,2,100\n"
        "2025-01-06,Widget,1,100\n"
        "2025-01-09,Widget,1,100\n",
        encoding="utf-8",
    )
    env = {"REPORT_FROM": "2025-01-02", "REPORT_TO": "2025-01-05"}
    rendered = _render(tmp_path, {"REPORT_CSV_PATH": "/x.csv", **env})
    assert rendered.endswith(" --from '2025-01-02' --to '2025-01-05'")
    data = _run(tmp_path, env, csv_path)
    assert [e["date"] for e in data] == ["2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]
    assert [e["orders"] for e in data] == [0, 1, 0, 0]


def test_only_one_bound_set(tmp_path: Path) -> None:
    rendered = _render(tmp_path, {"REPORT_CSV_PATH": "/x.csv", "REPORT_TO": "2025-01-05"})
    assert rendered.endswith("'/x.csv' --to '2025-01-05'")
    assert "--from" not in rendered


def test_single_quotes_stripped_from_range_values(tmp_path: Path) -> None:
    rendered = _render(tmp_path, {"REPORT_CSV_PATH": "/x.csv", "REPORT_FROM": "2025-01-01'; rm -rf /; '"})
    assert rendered.endswith(" --from '2025-01-01; rm -rf /; '")
    assert rendered.count("'") == 4  # only the path quotes and the flag value quotes remain


def test_invalid_range_rejected_by_cli_not_n8n(tmp_path: Path) -> None:
    env = {"REPORT_CSV_PATH": str(SAMPLE), "REPORT_FROM": "2025-13-01"}
    command = _render(tmp_path, env).replace("/app/src", str(ROOT / "src"))
    result = subprocess.run(command, shell=True, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stdout == ""


def test_in_range_gap_date_prints_no_sales(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    csv_path = tmp_path / "s.csv"
    csv_path.write_text("date,product,quantity,unit_price_cents\n2025-01-03,Widget,2,100\n", encoding="utf-8")
    data = _run(tmp_path, {"REPORT_FROM": "2025-01-02", "REPORT_TO": "2025-01-03"}, csv_path)
    assert data[0]["orders"] == 0
    harness = (
        "const fn = new Function('$input', process.argv[2]);\n"
        "const stdout = process.argv[3];\n"
        "console.log(fn({first: () => ({json: {stdout}})})[0].json.text);\n"
    )
    script = tmp_path / "h3.js"
    script.write_text(harness, encoding="utf-8")
    out = subprocess.run(
        [node, str(script), _format_code(), json.dumps(data)], capture_output=True, text=True, check=True
    )
    assert "2025-01-02: no sales" in out.stdout.splitlines()
