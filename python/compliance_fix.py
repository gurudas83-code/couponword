#!/usr/bin/env python3
"""
Coupon World Amazon trademark compliance migration.

Actions:
- Creates a timestamped backup of coupons.json
- Replaces Amazon-centric generic descriptions with retailer-neutral wording
- Removes unsupported "Amazon's Choice" badges
- Renames the generic "Amazon IN Fashion Fest" listing
- Updates product_engine.py so future generated descriptions remain neutral
- Writes JSON atomically
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
BACKUPS = ROOT / "backups"
PRODUCT_ENGINE = ROOT / "python" / "product_engine.py"

OLD_SENTENCE = (
    "Visit the Amazon IN product page to check the latest price, "
    "availability and offer details."
)

NEW_SENTENCE = (
    "Use the product link to check the latest price, availability "
    "and current offers from the retailer."
)

OLD_PRICE_TEXT = "Check live price on Amazon"
NEW_PRICE_TEXT = "Check latest price at retailer"

OLD_STORE = "Amazon IN"
NEUTRAL_STORE = "Online Retailer"


def load_products() -> list[dict[str, Any]]:
    data = json.loads(DB.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Every coupons.json entry must be an object.")
    return data


def backup_file(path: Path, label: str) -> Path:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = BACKUPS / f"{label}-{stamp}{path.suffix}"
    shutil.copy2(path, destination)
    return destination


def update_products(products: list[dict[str, Any]]) -> dict[str, int]:
    stats = {
        "descriptions": 0,
        "price_text": 0,
        "badges_removed": 0,
        "titles": 0,
        "stores": 0,
    }

    for product in products:
        description = str(product.get("description") or "")
        if OLD_SENTENCE in description:
            product["description"] = description.replace(
                OLD_SENTENCE,
                NEW_SENTENCE,
            )
            stats["descriptions"] += 1

        if product.get("priceText") == OLD_PRICE_TEXT:
            product["priceText"] = NEW_PRICE_TEXT
            stats["price_text"] += 1

        badge = str(product.get("badge") or "").strip()
        if badge.casefold() in {
            "amazon's choice",
            "amazons choice",
            "amazon choice",
        }:
            product.pop("badge", None)
            stats["badges_removed"] += 1

        if str(product.get("title") or "").strip() == "Amazon IN Fashion Fest":
            product["title"] = "Fashion Fest"
            stats["titles"] += 1

        # Keep real product names such as Amazon Basics, Kindle, Echo and
        # Fire TV unchanged. Only neutralise the generic marketplace label.
        if str(product.get("store") or "").strip() == OLD_STORE:
            product["store"] = NEUTRAL_STORE
            stats["stores"] += 1

    return stats


def save_products(products: list[dict[str, Any]]) -> None:
    temporary = DB.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Validate the completed temporary file before replacing the database.
    validated = json.loads(temporary.read_text(encoding="utf-8"))
    if not isinstance(validated, list) or len(validated) != len(products):
        temporary.unlink(missing_ok=True)
        raise ValueError("Temporary JSON validation failed.")

    temporary.replace(DB)


def update_future_generator() -> int:
    if not PRODUCT_ENGINE.exists():
        return 0

    text = PRODUCT_ENGINE.read_text(encoding="utf-8")
    updated = text.replace(OLD_SENTENCE, NEW_SENTENCE)

    # Also handle split Python string fragments if the same wording exists.
    updated = updated.replace(
        '"Visit the Amazon IN product page to check the latest price, "',
        '"Use the product link to check the latest price, availability "',
    ).replace(
        '"availability and offer details."',
        '"and current offers from the retailer."',
    )

    if updated == text:
        return 0

    backup_file(PRODUCT_ENGINE, "product-engine-before-compliance")
    PRODUCT_ENGINE.write_text(updated, encoding="utf-8")
    return 1


def main() -> int:
    products = load_products()
    database_backup = backup_file(DB, "coupons-before-compliance")

    stats = update_products(products)
    save_products(products)
    generator_updated = update_future_generator()

    print("=" * 64)
    print("COUPON WORLD COMPLIANCE MIGRATION")
    print("=" * 64)
    print("Products checked       :", len(products))
    print("Descriptions updated   :", stats["descriptions"])
    print("Price labels updated   :", stats["price_text"])
    print("Restricted badges gone :", stats["badges_removed"])
    print("Generic titles updated :", stats["titles"])
    print("Store labels neutral   :", stats["stores"])
    print("Future generator fixed :", "YES" if generator_updated else "NOT FOUND/NO CHANGE")
    print("Database backup        :", database_backup)
    print("JSON status            : VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
