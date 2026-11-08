import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

WORKFLOW = Path(__file__).resolve().parent.parent / "workflows" / "daily_report.json"


def load() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    return data


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


def test_manual_trigger_only() -> None:
    types = [n["type"] for n in load()["nodes"]]
    assert "n8n-nodes-base.manualTrigger" in types
    assert not any("schedule" in t.lower() or "cron" in t.lower() for t in types)


def test_chain_ends_in_telegram_and_runs_cli() -> None:
    nodes = {n["name"]: n for n in load()["nodes"]}
    assert nodes["Send Telegram"]["type"] == "n8n-nodes-base.telegram"
    assert "report.cli" in nodes["Run Report CLI"]["parameters"]["command"]


def test_no_token_shaped_string() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert not re.search(r"\d{6,}:[A-Za-z0-9_-]{30,}", text)


def test_chat_id_and_credentials_are_placeholders() -> None:
    tg = next(n for n in load()["nodes"] if n["type"] == "n8n-nodes-base.telegram")
    assert tg["parameters"]["chatId"] == "REPLACE_WITH_TELEGRAM_CHAT_ID"
    cred = tg["credentials"]["telegramApi"]
    assert cred["id"].startswith("REPLACE_WITH_")
    assert cred["name"].startswith("REPLACE_WITH_")


def _format_code() -> str:
    for node in load()["nodes"]:
        if node["name"] == "Format Message":
            code: str = node["parameters"]["jsCode"]
            return code
    raise AssertionError("Format Message node not found")


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
