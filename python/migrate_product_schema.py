#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "coupons.json"
BACKUP_DIR = ROOT / "backups"

SCHEMA_FIELDS = (
    "id",
    "asin",
    "title",
    "brand",
    "category",
    "description",
    "image",
    "link",
    "store",
    "active",
    "availability",
    "data_source",
    "price",
    "mrp",
    "save",
    "discount",
    "priceText",
    "currency",
    "last_checked",
    "code",
    "expiry",
    "badge",
    "linkType",
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def normalize_number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return value

    text = clean_text(value)
    text = (
        text.replace("₹", "")
        .replace(",", "")
        .replace("%", "")
        .strip()
    )

    try:
        number = float(text)
    except ValueError:
        return None

    return int(number) if number.is_integer() else number


def load_products() -> list[dict[str, Any]]:
    data = json.loads(DB_FILE.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list.")

    for index, product in enumerate(data, start=1):
        if not isinstance(product, dict):
            raise ValueError(
                f"Product {index} is invalid. Every product must be an object."
            )

    return data


def normalize_product(
    product: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    defaults = {
        "id": product.get("id") or product.get("sl_no") or index,
        "asin": clean_text(product.get("asin")).upper() or None,
        "title": clean_text(product.get("title")),
        "brand": clean_text(product.get("brand")) or None,
        "category": clean_text(product.get("category")) or "Uncategorized",
        "description": clean_text(product.get("description")) or None,
        "image": clean_text(product.get("image")) or None,
        "link": clean_text(product.get("link")),
        "store": clean_text(product.get("store")) or None,
        "active": product.get("active") is not False,
        "availability": (
            clean_text(product.get("availability"))
            or "Check retailer"
        ),
        "data_source": (
            clean_text(product.get("data_source"))
            or "legacy"
        ),
        "price": normalize_number(product.get("price")),
        "mrp": normalize_number(product.get("mrp")),
        "save": normalize_number(product.get("save")),
        "discount": clean_text(product.get("discount")) or None,
        "priceText": (
            clean_text(product.get("priceText"))
            or "Check latest price"
        ),
        "currency": clean_text(product.get("currency")) or "INR",
        "last_checked": clean_text(product.get("last_checked")) or None,
        "code": clean_text(product.get("code")) or None,
        "expiry": clean_text(product.get("expiry")) or None,
        "badge": clean_text(product.get("badge")) or None,
        "linkType": clean_text(product.get("linkType")) or None,
    }

    for field in SCHEMA_FIELDS:
        normalized[field] = defaults[field]

    # Preserve unknown fields so migration never deletes existing data.
    for key, value in product.items():
        if key not in normalized:
            normalized[key] = value

    return normalized


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"coupons-before-schema-{timestamp}.json"

    shutil.copy2(DB_FILE, backup)
    return backup


def save_products(products: list[dict[str, Any]]) -> None:
    temporary = DB_FILE.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    temporary.replace(DB_FILE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize Coupon World product schema safely."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write normalized products to coupons.json.",
    )
    args = parser.parse_args()

    products = load_products()

    normalized = [
        normalize_product(product, index)
        for index, product in enumerate(products, start=1)
    ]

    changed = sum(
        original != updated
        for original, updated in zip(products, normalized)
    )

    print("=" * 64)
    print("COUPON WORLD PRODUCT SCHEMA MIGRATION")
    print("=" * 64)
    print("Products found   :", len(products))
    print("Products changed :", changed)
    print("Schema fields    :", len(SCHEMA_FIELDS))
    print("Write mode       :", "YES" if args.write else "NO")

    print("\nFirst product fields:")
    for field in normalized[0].keys() if normalized else []:
        print("-", field)

    if not args.write:
        print("\nDRY RUN: coupons.json was not changed.")
        print("Review the output, then run with --write.")
        return 0

    backup = create_backup()
    save_products(normalized)

    print("\nMIGRATION COMPLETE")
    print("Backup created   :", backup.relative_to(ROOT))
    print("Database updated :", DB_FILE.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
