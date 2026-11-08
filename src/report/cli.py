"""CLI: read a sales CSV and print one JSON summary per date."""

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict

from report.summary import SaleRow, summarize


def read_rows(path: str) -> list[SaleRow]:
    rows: list[SaleRow] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for r in reader:
            missing = [k for k, v in r.items() if v is None]
            if missing:
                raise ValueError(
                    f"line {reader.line_num}: missing field(s): {', '.join(missing)}"
                )
            rows.append(
                SaleRow(
                    date=r["date"],
                    product=r["product"],
                    quantity=int(r["quantity"]),
                    unit_price_cents=int(r["unit_price_cents"]),
                )
            )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="report.cli", description=__doc__)
    parser.add_argument("csv_path", help="path to the sales CSV file")
    args = parser.parse_args(argv)
    try:
        rows = read_rows(args.csv_path)
    except FileNotFoundError:
        print(f"error: file not found: {args.csv_path}", file=sys.stderr)
        return 2
    except (OSError, KeyError, ValueError) as exc:
        print(f"error: cannot read {args.csv_path}: {exc}", file=sys.stderr)
        return 1
    by_date: dict[str, list[SaleRow]] = defaultdict(list)
    for row in rows:
        by_date[row.date].append(row)
    result = [
        {"date": d, **asdict(summarize(by_date[d]))} for d in sorted(by_date)
    ]
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
