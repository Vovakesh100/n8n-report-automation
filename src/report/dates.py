"""Date range logic. Pure, no I/O."""

from collections.abc import Iterable
from datetime import date, timedelta


def parse_date(value: str) -> date:
    """Parse a strict YYYY-MM-DD string; raise ValueError otherwise."""
    if len(value) != 10:
        raise ValueError(f"invalid date {value!r}, expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid date {value!r}, expected YYYY-MM-DD") from None


def date_range(
    present: Iterable[str], start: str | None = None, end: str | None = None
) -> list[str]:
    """Return every ISO date from start to end inclusive.

    Missing bounds default to the min and max of `present`. If a bound is
    missing and `present` is empty, the result is empty. Raises ValueError
    for an invalid date or when start is after end.
    """
    known = [parse_date(d) for d in present]
    first = parse_date(start) if start is not None else (min(known) if known else None)
    last = parse_date(end) if end is not None else (max(known) if known else None)
    if first is None or last is None:
        return []
    if first > last:
        raise ValueError(f"--from {first} is after --to {last}")
    return [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]
