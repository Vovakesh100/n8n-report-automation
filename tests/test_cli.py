import json
import subprocess
import sys
from pathlib import Path

from report.cli import main

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_sales.csv"


def _dates() -> list[str]:
    lines = SAMPLE.read_text().splitlines()[1:]
    return sorted({line.split(",")[0] for line in lines if line})


def test_module_prints_valid_json() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "report.cli", str(SAMPLE)],
        capture_output=True,
        check=False,
        text=True,
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
