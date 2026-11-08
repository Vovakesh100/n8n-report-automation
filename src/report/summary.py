"""Daily summary computed from sales rows. Pure, no I/O."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class SaleRow:
    """One sales row. Money is in integer cents."""

    date: str
    product: str
    quantity: int
    unit_price_cents: int


@dataclass(frozen=True)
class DailySummary:
    """Summary for one date. `orders` is the number of input rows."""

    total_revenue_cents: int
    orders: int
    top_product: str | None


def summarize(rows: Iterable[SaleRow]) -> DailySummary:
    """Summarize rows for a single date.

    Top product is the one with the highest revenue; ties go to the
    product name in ascending order. Empty input gives no top product.
    """
    total = 0
    orders = 0
    by_product: dict[str, int] = {}
    for row in rows:
        revenue = row.quantity * row.unit_price_cents
        total += revenue
        orders += 1
        by_product[row.product] = by_product.get(row.product, 0) + revenue
    top: str | None = None
    if by_product:
        top = min(by_product, key=lambda name: (-by_product[name], name))
    return DailySummary(total_revenue_cents=total, orders=orders, top_product=top)
