import json
import re
from pathlib import Path
from typing import Any

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
