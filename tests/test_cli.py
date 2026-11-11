import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from report.cli import main

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sample_sales.csv"
# The subprocess must import report from src/, even when pytest runs without PYTHONPATH.
CHILD_ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def _dates() -> list[str]:
    lines = SAMPLE.read_text().splitlines()[1:]
    return sorted({line.split(",")[0] for line in lines if line})


def test_module_prints_valid_json() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "report.cli", str(SAMPLE)],
        capture_output=True,
        check=False,
        text=True,
        env=CHILD_ENV,
    )
    assert proc.returncode == 0
    assert isinstance(json.loads(proc.stdout), list)


def test_one_entry_per_date_sorted(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main([str(SAMPLE)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [e["date"] for e in data] == _dates()
    for e in data:
        assert isinstance(e["total_revenue_cents"], int)
        assert isinstance(e["orders"], int)


def test_missing_file(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    code = main([str(tmp_path / "nope.csv")])
    captured = capsys.readouterr()
    assert code != 0
    assert "nope.csv" in captured.err
    assert captured.out == ""


def test_sample_dates_give_different_summaries(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main([str(SAMPLE)]) == 0
    data = json.loads(capsys.readouterr().out)
    distinct = {
        (e["total_revenue_cents"], e["orders"], e["top_product"]) for e in data
    }
    assert len(distinct) >= 2


def test_short_row_reports_line_and_fails(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "short.csv"
    path.write_text(
        "date,product,quantity,unit_price_cents\n"
        "2025-01-01,widget,1,250\n"
        "2025-01-01,gadget,2\n"
    )
    proc = subprocess.run(
        [sys.executable, "-m", "report.cli", str(path)],
        capture_output=True,
        check=False,
        text=True,
        env=CHILD_ENV,
    )
    assert proc.returncode != 0
    assert "line 3" in proc.stderr
    assert "unit_price_cents" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert proc.stdout == ""


def _csv(tmp_path: Path, dates: list[str]) -> Path:
    path = tmp_path / "s.csv"
    lines = ["date,product,quantity,unit_price_cents"]
    lines += [f"{d},Widget,2,150" for d in dates]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_gap_date_inside_range_has_zero_entry(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, ["2025-01-01", "2025-01-03"])
    assert main([str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [e["date"] for e in data] == ["2025-01-01", "2025-01-02", "2025-01-03"]
    assert data[1] == {
        "date": "2025-01-02",
        "total_revenue_cents": 0,
        "orders": 0,
        "top_product": None,
    }


def test_date_with_orders_unchanged(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, ["2025-01-01", "2025-01-03"])
    assert main([str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0] == {
        "date": "2025-01-01",
        "total_revenue_cents": 300,
        "orders": 1,
        "top_product": "Widget",
    }


def test_from_to_extend_range(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, ["2025-01-02"])
    assert main([str(path), "--from", "2025-01-01", "--to", "2025-01-03"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [e["date"] for e in data] == ["2025-01-01", "2025-01-02", "2025-01-03"]
    assert [e["orders"] for e in data] == [0, 1, 0]


def test_empty_file_still_empty_list(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, [])
    assert main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out) == []


@pytest.mark.parametrize(
    "args",
    [
        ["--from", "2025-13-01"],
        ["--to", "not-a-date"],
        ["--from", "2025-1-1"],
        ["--from", "2025-01-05", "--to", "2025-01-01"],
    ],
)
def test_invalid_date_args(capsys, tmp_path, args) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, ["2025-01-02"])
    code = main([str(path), *args])
    captured = capsys.readouterr()
    assert code != 0
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_from_to_print_only_dates_inside_range(capsys, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _csv(tmp_path, ["2025-01-01", "2025-01-03", "2025-01-06", "2025-01-09"])
    assert main([str(path), "--from", "2025-01-02", "--to", "2025-01-05"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [e["date"] for e in data] == ["2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]
    assert [e["orders"] for e in data] == [0, 1, 0, 0]
