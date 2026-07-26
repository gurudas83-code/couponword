#!/usr/bin/env python3
"""
Coupon World AI OS
Price Importer v0.1

Purpose:
- Read verified price updates from a CSV file
- Validate product IDs and prices
- Update coupons.json safely
- Create a timestamped backup before writing
- Support dry-run mode by default
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
BACKUP_DIR = ROOT / ".price_backups"


def normalize_price(value: object) -> float | None:
    if value in (None, ""):
        return None

    text = str(value).strip()
    text = text.replace("₹", "").replace(",", "")

    try:
        price = float(text)
    except ValueError:
        return None

    if price < 0:
        return None

    return price


def load_products() -> list[dict]:
    data = json.loads(DB.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")

    return data


def load_updates(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    updates = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        required_fields = {"id", "price", "mrp"}

        if not reader.fieldnames:
            raise ValueError("CSV file has no header")

        missing_fields = required_fields - set(reader.fieldnames)

        if missing_fields:
            raise ValueError(
                "CSV missing required columns: "
                + ", ".join(sorted(missing_fields))
            )

        for row_number, row in enumerate(reader, start=2):
            product_id = str(row.get("id", "")).strip()

            if not product_id:
                print(f"SKIP row {row_number}: product ID missing")
                continue

            price = normalize_price(row.get("price"))
            mrp = normalize_price(row.get("mrp"))

            if price is None:
                print(f"SKIP row {row_number}: invalid price")
                continue

            if mrp is not None and price > mrp:
                print(
                    f"SKIP row {row_number}: "
                    f"price {price} is greater than MRP {mrp}"
                )
                continue

            updates.append(
                {
                    "id": product_id,
                    "price": price,
                    "mrp": mrp,
                }
            )

    return updates


def find_product(products: list[dict], product_id: str) -> dict | None:
    for product in products:
        existing_id = product.get("id") or product.get("sl_no")

        if str(existing_id).strip() == product_id:
            return product

    return None


def apply_updates(
    products: list[dict],
    updates: list[dict],
) -> tuple[int, int]:
    updated = 0
    not_found = 0

    for update in updates:
        product = find_product(products, update["id"])

        if product is None:
            print(f"NOT FOUND: Product ID {update['id']}")
            not_found += 1
            continue

        old_price = product.get("price")
        old_mrp = product.get("mrp")

        product["price"] = update["price"]
        product["mrp"] = update["mrp"]

        print(
            f"UPDATE ID {update['id']}: "
            f"price {old_price} -> {update['price']}, "
            f"mrp {old_mrp} -> {update['mrp']}"
        )

        updated += 1

    return updated, not_found


def create_backup() -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"coupons_{timestamp}.json"

    shutil.copy2(DB, backup_path)

    return backup_path


def save_products(products: list[dict]) -> None:
    temp_path = DB.with_suffix(".json.tmp")

    temp_path.write_text(
        json.dumps(products, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    temp_path.replace(DB)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import verified product prices into coupons.json"
    )

    parser.add_argument(
        "csv_file",
        help="Path to the verified price CSV file",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply updates to coupons.json",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv_file)

    products = load_products()
    updates = load_updates(csv_path)

    print("=" * 64)
    print("COUPON WORLD PRICE IMPORTER")
    print("=" * 64)
    print("Products loaded :", len(products))
    print("Valid updates   :", len(updates))
    print("Mode            :", "WRITE" if args.write else "DRY RUN")
    print("-" * 64)

    updated, not_found = apply_updates(products, updates)

    print("-" * 64)
    print("Products updated :", updated)
    print("IDs not found    :", not_found)

    if not args.write:
        print("\nDRY RUN ONLY: coupons.json was not changed.")
        print("Use --write after reviewing the output.")
        return 0

    if updated == 0:
        print("\nNo valid updates found. Nothing was written.")
        return 0

    backup_path = create_backup()
    save_products(products)

    print("\nWRITE COMPLETE")
    print("Backup :", backup_path)
    print("Updated:", DB)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())