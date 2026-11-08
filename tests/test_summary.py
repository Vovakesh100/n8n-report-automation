import csv
from pathlib import Path

from report.summary import SaleRow, summarize


def row(product: str, qty: int, price: int) -> SaleRow:
    return SaleRow("2025-01-01", product, qty, price)


def test_revenue_is_integer_quantity_times_price() -> None:
    result = summarize([row("widget", 3, 250), row("gadget", 2, 1299)])
    assert result.total_revenue_cents == 3 * 250 + 2 * 1299
    assert isinstance(result.total_revenue_cents, int)
    assert result.orders == 2


def test_empty_input() -> None:
    result = summarize([])
    assert result.total_revenue_cents == 0
    assert result.orders == 0
    assert result.top_product is None


def test_top_product_by_revenue_aggregates_rows() -> None:
    result = summarize([row("a", 1, 100), row("a", 1, 100), row("b", 1, 150)])
    assert result.top_product == "a"


def test_tie_resolved_by_name_ascending() -> None:
    result = summarize([row("zeta", 1, 500), row("alpha", 1, 500), row("mid", 1, 100)])
    assert result.top_product == "alpha"
    assert summarize([row("alpha", 1, 500), row("zeta", 1, 500)]).top_product == "alpha"


def test_sample_data_runs() -> None:
    with Path("data/sample_sales.csv").open() as f:
        rows = [
            SaleRow(r["date"], r["product"], int(r["quantity"]), int(r["unit_price_cents"]))
            for r in csv.DictReader(f)
            if r["date"] == "2025-01-01"
        ]
    result = summarize(rows)
    assert result.orders == len(rows) > 0
    assert result.top_product is not None
