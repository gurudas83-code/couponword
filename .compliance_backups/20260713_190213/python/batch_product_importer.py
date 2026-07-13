#!/usr/bin/env python3
"""
Coupon World AI OS
Batch Product Importer v0.1

Two safe modes:

1) Prepare a CSV template from Amazon URLs:
   python python/batch_product_importer.py prepare product_queue.txt products_import.csv

2) Preview or write completed CSV rows:
   python python/batch_product_importer.py import products_import.csv
   python python/batch_product_importer.py import products_import.csv --write

Rules:
- Never invents title, category, price, image, discount, rating, reviews, stock, or urgency.
- Skips invalid URLs and database duplicates.
- Requires a verified title before write.
- Creates a backup before changing coupons.json.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from amazon_data_provider import get_default_provider
from batch_product_queue import read_urls, scan_urls
from product_engine import (
    COUPONS_FILE,
    clean_text,
    create_backup,
    detect_brand,
    generate_description,
    load_json,
    save_json,
)
from product_pipeline import (
    build_affiliate_url,
    existing_asin,
    extract_asin,
    next_product_id,
    validate_url,
)

CSV_FIELDS = ["asin", "url", "title", "category"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and safely import Amazon product batches."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Create a CSV template from a text file of Amazon URLs.",
    )
    prepare.add_argument("input_file", type=Path)
    prepare.add_argument("output_csv", type=Path)

    importer = subparsers.add_parser(
        "import",
        help="Preview or import completed product rows from CSV.",
    )
    importer.add_argument("input_csv", type=Path)
    importer.add_argument(
        "--write",
        action="store_true",
        help="Write valid, non-duplicate rows to coupons.json.",
    )

    return parser.parse_args()


def prepare_csv(input_file: Path, output_csv: Path) -> int:
    products = load_json(COUPONS_FILE)
    existing_asins = {
        asin for product in products if (asin := existing_asin(product))
    }

    rows = read_urls(input_file)
    results = scan_urls(rows, existing_asins)
    ready = [item for item in results if item.status == "READY"]

    with output_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for item in ready:
            writer.writerow(
                {
                    "asin": item.asin,
                    "url": item.raw_url,
                    "title": "",
                    "category": "",
                }
            )

    print("\nBATCH CSV PREPARED")
    print(f"URLs scanned       : {len(results)}")
    print(f"Ready rows written : {len(ready)}")
    print(f"Output file        : {output_csv}")
    print("Database changed   : NO")
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        missing_columns = [
            field for field in CSV_FIELDS if field not in (reader.fieldnames or [])
        ]
        if missing_columns:
            raise ValueError(
                "Missing required CSV columns: " + ", ".join(missing_columns)
            )

        return [
            {key: clean_text(value) for key, value in row.items()}
            for row in reader
        ]


def build_record(
    products: list[dict[str, Any]],
    asin: str,
    title: str,
    category: str,
) -> dict[str, Any]:
    provider = get_default_provider()
    data = provider.get_product(
        asin,
        title=title,
        category=category,
    )

    brand = clean_text(data.brand) or detect_brand(data.title)

    product: dict[str, Any] = {
        "id": next_product_id(products),
        "asin": data.asin,
        "store": "Amazon IN",
        "title": clean_text(data.title),
        "brand": brand,
        "category": clean_text(data.category),
        "price": clean_text(data.price),
        "mrp": clean_text(data.mrp),
        "save": "",
        "discount": clean_text(data.discount),
        "image": clean_text(data.image),
        "link": build_affiliate_url(data.asin),
        "description": "",
        "data_source": data.source,
    }

    if product["title"]:
        product["description"] = generate_description(product, brand)

    return product


def import_csv(input_csv: Path, write: bool) -> int:
    products = load_json(COUPONS_FILE)
    rows = read_csv_rows(input_csv)

    existing_asins = {
        asin for product in products if (asin := existing_asin(product))
    }
    seen_batch: set[str] = set()

    ready: list[dict[str, Any]] = []
    skipped: list[tuple[int, str]] = []

    for row_number, row in enumerate(rows, start=2):
        raw_url = row.get("url", "")
        csv_asin = row.get("asin", "").upper()
        title = row.get("title", "")
        category = row.get("category", "")

        try:
            validated_url = validate_url(raw_url)
            url_asin = extract_asin(validated_url)

            if csv_asin and csv_asin != url_asin:
                raise ValueError(
                    f"CSV ASIN {csv_asin} does not match URL ASIN {url_asin}."
                )

            asin = url_asin

            if asin in existing_asins:
                skipped.append((row_number, "database duplicate"))
                continue

            if asin in seen_batch:
                skipped.append((row_number, "batch duplicate"))
                continue

            if not title:
                skipped.append((row_number, "verified title missing"))
                continue

            seen_batch.add(asin)
            record = build_record(products + ready, asin, title, category)
            ready.append(record)

        except ValueError as error:
            skipped.append((row_number, str(error)))

    print("\n" + "=" * 68)
    print("COUPON WORLD BATCH IMPORT PREVIEW")
    print("=" * 68)
    print(f"CSV rows          : {len(rows)}")
    print(f"Ready to import   : {len(ready)}")
    print(f"Skipped           : {len(skipped)}")
    print(f"Write mode        : {'YES' if write else 'NO'}")
    print("=" * 68)

    for product in ready:
        print(
            f"READY | ID {product['id']} | {product['asin']} | "
            f"{product['title']} | {product['category'] or '[NO CATEGORY]'}"
        )

    for row_number, reason in skipped:
        print(f"SKIP  | CSV row {row_number} | {reason}")

    if not write:
        print("\nDRY RUN: coupons.json was not changed.")
        return 0

    if not ready:
        print("\nNo valid new products were available to write.")
        return 0

    backup_file = create_backup(COUPONS_FILE)
    products.extend(ready)
    save_json(COUPONS_FILE, products)

    print("\nBATCH IMPORT COMPLETE")
    print(f"Backup created   : {backup_file.relative_to(COUPONS_FILE.parent)}")
    print(f"Products added   : {len(ready)}")
    print(f"Products after   : {len(products)}")
    print("Database changed : YES")
    return 0


def main() -> int:
    args = parse_arguments()

    try:
        if args.command == "prepare":
            return prepare_csv(args.input_file, args.output_csv)

        if args.command == "import":
            return import_csv(args.input_csv, args.write)

        raise ValueError(f"Unsupported command: {args.command}")

    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
