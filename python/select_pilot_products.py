#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "coupons.json"


def useful(value):
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {
        "none", "null", "n/a", "na", "unknown"
    }


data = json.loads(
    CATALOG.read_text(encoding="utf-8-sig")
)

if isinstance(data, dict):
    products = data.get("products", data.get("coupons", []))
else:
    products = data


candidates = []

for product in products:
    asin = str(product.get("asin") or "").strip()
    brand = str(product.get("brand") or "").strip()
    title = str(product.get("title") or "").strip()
    category = str(product.get("category") or "").strip()
    product_id = str(product.get("id") or "").strip()

    if not (
        useful(product_id)
        and useful(asin)
        and useful(brand)
        and useful(title)
    ):
        continue

    # Samsung M36 is already our first pilot product.
    if asin.upper() == "B0FDBB2VRC":
        continue

    score = 0

    if useful(category):
        score += 1

    if useful(product.get("image")):
        score += 1

    if useful(product.get("availability")):
        score += 1

    if useful(product.get("link")):
        score += 1

    candidates.append(
        {
            "score": score,
            "id": product_id,
            "asin": asin,
            "brand": brand,
            "title": title,
            "category": category,
        }
    )


candidates.sort(
    key=lambda x: (-x["score"], x["id"])
)


print()
print("=" * 90)
print("COUPON WORLD - 5 PRODUCT PILOT CANDIDATES")
print("=" * 90)

print()
print("PRODUCT 1 - ALREADY VERIFIED")
print("ID       : 72")
print("Brand    : Samsung")
print("Model    : Galaxy M36 5G")
print("Variant  : 6GB/128GB")
print("ASIN     : B0FDBB2VRC")

print()
print("-" * 90)
print("NEXT BEST CANDIDATES FROM EXISTING CATALOG")
print("-" * 90)

for number, item in enumerate(candidates[:10], start=2):
    print()
    print("Candidate :", number)
    print("ID        :", item["id"])
    print("ASIN      :", item["asin"])
    print("Brand     :", item["brand"])
    print("Category  :", item["category"])
    print("Title     :", item["title"])
    print("Score     :", item["score"])

print()
print("Total usable ASIN candidates :", len(candidates))
