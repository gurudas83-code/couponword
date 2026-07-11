#!/usr/bin/env python3
"""
Coupon World AI OS
Batch Product Queue Scanner v0.1

Purpose:
- Read Amazon India URLs from a text file
- Extract ASINs
- Reject invalid/unsupported URLs
- Detect duplicates against coupons.json
- Produce a safe preview queue
- Never modify coupons.json
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from product_engine import COUPONS_FILE, load_json
from product_pipeline import extract_asin, validate_url, existing_asin


@dataclass(slots=True)
class QueueItem:
    line_number: int
    raw_url: str
    status: str
    asin: str = ""
    reason: str = ""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a batch of Amazon India URLs without changing coupons.json."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Text file containing one Amazon URL per line.",
    )
    return parser.parse_args()


def read_urls(path: Path) -> list[tuple[int, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    rows: list[tuple[int, str]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            value = raw_line.strip()

            if not value or value.startswith("#"):
                continue

            rows.append((line_number, value))

    return rows


def scan_urls(
    rows: Iterable[tuple[int, str]],
    existing_asins: set[str],
) -> list[QueueItem]:
    results: list[QueueItem] = []
    seen_in_batch: set[str] = set()

    for line_number, raw_url in rows:
        try:
            validated_url = validate_url(raw_url)
            asin = extract_asin(validated_url)

            if asin in existing_asins:
                results.append(
                    QueueItem(
                        line_number=line_number,
                        raw_url=raw_url,
                        status="DUPLICATE_DATABASE",
                        asin=asin,
                    )
                )
                continue

            if asin in seen_in_batch:
                results.append(
                    QueueItem(
                        line_number=line_number,
                        raw_url=raw_url,
                        status="DUPLICATE_BATCH",
                        asin=asin,
                    )
                )
                continue

            seen_in_batch.add(asin)
            results.append(
                QueueItem(
                    line_number=line_number,
                    raw_url=raw_url,
                    status="READY",
                    asin=asin,
                )
            )

        except ValueError as error:
            results.append(
                QueueItem(
                    line_number=line_number,
                    raw_url=raw_url,
                    status="INVALID",
                    reason=str(error),
                )
            )

    return results


def print_report(results: list[QueueItem]) -> None:
    counts = {
        "READY": 0,
        "DUPLICATE_DATABASE": 0,
        "DUPLICATE_BATCH": 0,
        "INVALID": 0,
    }

    for item in results:
        counts[item.status] += 1

    print("\n" + "=" * 68)
    print("COUPON WORLD BATCH PRODUCT QUEUE")
    print("=" * 68)
    print(f"URLs received       : {len(results)}")
    print(f"Ready new ASINs     : {counts['READY']}")
    print(f"Database duplicates : {counts['DUPLICATE_DATABASE']}")
    print(f"Batch duplicates    : {counts['DUPLICATE_BATCH']}")
    print(f"Invalid URLs        : {counts['INVALID']}")
    print("Database changed    : NO")
    print("=" * 68)

    for item in results:
        label = f"Line {item.line_number}: {item.status}"

        if item.asin:
            label += f" | ASIN {item.asin}"

        print(label)

        if item.reason:
            print(f"  Reason: {item.reason}")


def main() -> int:
    args = parse_arguments()

    try:
        rows = read_urls(args.input_file)
        products = load_json(COUPONS_FILE)
        existing_asins = {
            asin
            for product in products
            if (asin := existing_asin(product))
        }

        results = scan_urls(rows, existing_asins)
        print_report(results)
        return 0

    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
