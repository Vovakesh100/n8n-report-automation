import csv
from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_sales.csv"


def _rows() -> list[dict[str, str]]:
    with SAMPLE.open(newline="") as f:
        return list(csv.DictReader(f))


def test_header_and_row_count() -> None:
    with SAMPLE.open(newline="") as f:
        header = next(csv.reader(f))
    assert header == ["date", "product", "quantity", "unit_price_cents"]
    assert len(_rows()) >= 20


def test_unit_price_cents_non_negative_integers() -> None:
    for row in _rows():
        value = row["unit_price_cents"]
        assert value.isdigit(), value
        assert int(value) >= 0


def test_covers_three_days_and_three_products() -> None:
    rows = _rows()
    assert len({r["date"] for r in rows}) >= 3
    assert len({r["product"] for r in rows}) >= 3
