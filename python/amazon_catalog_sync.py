#!/usr/bin/env python3
"""
Coupon World AI OS
Amazon Catalog Sync v0.1

Dry-run by default.
Today it exits safely because the configured provider has no API access.
Later a CreatorsApiProvider can supply image, price, MRP and availability,
and this same command can run on a schedule.
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from amazon_data_provider import get_default_provider

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
BACKUPS = ROOT / "backups"


def load_products():
    data = json.loads(DB.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")
    return data


def backup():
    BACKUPS.mkdir(parents=True, exist_ok=True)
    p = BACKUPS / f"coupons-before-amazon-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    shutil.copy2(DB, p)
    return p


def save(products):
    tmp = DB.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(DB)


def calculate(price, mrp):
    if price in (None, "") or mrp in (None, ""):
        return None, None
    price = float(price)
    mrp = float(mrp)
    if price <= 0 or mrp < price:
        return None, None
    saving = mrp - price
    saving = int(saving) if saving.is_integer() else round(saving, 2)
    discount = round((saving / mrp) * 100)
    return saving, f"{discount}% OFF" if discount else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    provider = get_default_provider()
    products = load_products()

    print("=" * 64)
    print("AMAZON CATALOG SYNC")
    print("=" * 64)
    print("Provider      :", getattr(provider, "name", "unknown"))
    print("API available :", "YES" if getattr(provider, "api_available", False) else "NO")

    if not getattr(provider, "api_available", False):
        print("Database      : NOT CHANGED")
        print("Status        : Ready for future Creators API connection")
        return 0

    selected = products[:args.limit] if args.limit else products
    changes = []

    for index, product in enumerate(selected):
        asin = str(product.get("asin", "")).strip().upper()
        if not asin:
            continue

        live = provider.get_product(
            asin,
            title=str(product.get("title", "") or ""),
            brand=str(product.get("brand", "") or ""),
            category=str(product.get("category", "") or ""),
        )

        proposed = dict(product)
        changed = []

        for field in ("title", "brand", "category", "image"):
            value = getattr(live, field, "")
            if value and proposed.get(field) != value:
                proposed[field] = value
                changed.append(field)

        availability = str(getattr(live, "availability", "") or "").lower()

        if availability in {"available", "in_stock", "instock"}:
            for field, value in (("availability", "available"), ("active", True)):
                if proposed.get(field) != value:
                    proposed[field] = value
                    changed.append(field)

            for field in ("price", "mrp"):
                value = getattr(live, field, None)
                if value not in (None, "") and proposed.get(field) != value:
                    proposed[field] = value
                    changed.append(field)

            saving, discount = calculate(proposed.get("price"), proposed.get("mrp"))
            if proposed.get("save") != saving:
                proposed["save"] = saving
                changed.append("save")
            if proposed.get("discount") != discount:
                proposed["discount"] = discount
                changed.append("discount")

        elif availability in {"unavailable", "out_of_stock", "outofstock"}:
            for field, value in (("availability", "unavailable"), ("active", False)):
                if proposed.get(field) != value:
                    proposed[field] = value
                    changed.append(field)
            for field in ("price", "mrp", "save", "discount"):
                if proposed.get(field) is not None:
                    proposed[field] = None
                    changed.append(field)

        if changed:
            proposed["amazon_checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            changes.append((index, proposed, changed))

    print("Products checked :", len(selected))
    print("Products changed :", len(changes))
    print("Write mode       :", "YES" if args.write else "NO")

    for _, product, fields in changes:
        print("UPDATE |", product.get("asin"), "|", ", ".join(fields))

    if not args.write:
        print("DRY RUN: coupons.json was not changed.")
        return 0

    if not changes:
        print("No verified changes available.")
        return 0

    b = backup()
    for index, proposed, _ in changes:
        products[index] = proposed
    save(products)

    print("SYNC COMPLETE")
    print("Backup created:", b.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
