#!/usr/bin/env python3
"""
=========================================================
Coupon World AI OS
Product Engine v1.0
=========================================================

Purpose:
- Load Product Database
- Validate Products
- Calculate Database Health
- Generate Product Intelligence Report

Author : Coupon World AI OS
"""

import json
from pathlib import Path
import json
from pathlib import Path

KNOWN_BRANDS = {
    "boat": "boAt",
    "apple": "Apple",
    "samsung": "Samsung",
    "redmi": "Redmi",
    "realme": "realme",
    "noise": "Noise",
    "fire-boltt": "Fire-Boltt",
    "fireboltt": "Fire-Boltt",
    "oneplus": "OnePlus",
    "oppo": "OPPO",
    "vivo": "Vivo",
    "xiaomi": "Xiaomi",
    "hp": "HP",
    "dell": "Dell",
    "lenovo": "Lenovo",
    "asus": "ASUS",
    "acer": "Acer",
    "sony": "Sony",
    "jbl": "JBL",
    "anker": "Anker",
    "amazon": "Amazon"
}

# -------------------------------------------------------
# FILE LOCATIONS
# -------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

COUPONS_FILE = ROOT / "coupons.json"

PRODUCT_SCHEMA = ROOT / "database" / "product-schema.json"
CATEGORY_SCHEMA = ROOT / "database" / "category-schema.json"
BRAND_SCHEMA = ROOT / "database" / "brand-schema.json"


# -------------------------------------------------------
# LOAD JSON
# -------------------------------------------------------

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------------------------------
# BRAND DETECTION
# -------------------------------------------------------

def detect_brand(title):

    title = str(title).lower()

    for key, brand in KNOWN_BRANDS.items():
        if key in title:
            return brand

    return ""
# -------------------------------------------------------
# DATABASE HEALTH
# -------------------------------------------------------

def calculate_health(report):

    total_checks = (
        report["products"] * 5
    )

    failed = (
        report["missing_brand"]
        + report["missing_category"]
        + report["missing_image"]
        + report["missing_description"]
        + report["missing_link"]
    )

    score = max(0, round((1 - failed / total_checks) * 100))

    return score


# -------------------------------------------------------
# VALIDATION
# -------------------------------------------------------

def validate_products(products):

    report = {
        "products": len(products),
        "complete": 0,
        "incomplete": 0,
        "missing_brand": 0,
        "missing_category": 0,
        "missing_image": 0,
        "missing_description": 0,
        "missing_link": 0
    }

    for product in products:

        complete = True

        if not product.get("brand"):
            report["missing_brand"] += 1
            complete = False

        if not product.get("category"):
            report["missing_category"] += 1
            complete = False

        if not product.get("image"):
            report["missing_image"] += 1
            complete = False

        if not product.get("description"):
            report["missing_description"] += 1
            complete = False

        if not product.get("link"):
            report["missing_link"] += 1
            complete = False

        if complete:
            report["complete"] += 1
        else:
            report["incomplete"] += 1

    report["health"] = calculate_health(report)

    return report


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():

    print("=" * 55)
    print("Coupon World AI OS")
    print("Product Engine v1.0")
    print("=" * 55)

    # Load schemas (used in future versions)
    product_schema = load_json(PRODUCT_SCHEMA)
    category_schema = load_json(CATEGORY_SCHEMA)
    brand_schema = load_json(BRAND_SCHEMA)

    products = load_json(COUPONS_FILE)

    report = validate_products(products)

    print()

    print(f"Products Found      : {report['products']}")
    print(f"Complete Products   : {report['complete']}")
    print(f"Incomplete Products : {report['incomplete']}")

    print()

    print(f"Missing Brand       : {report['missing_brand']}")
    print(f"Missing Category    : {report['missing_category']}")
    print(f"Missing Image       : {report['missing_image']}")
    print(f"Missing Description : {report['missing_description']}")
    print(f"Missing Link        : {report['missing_link']}")

    print()

    print(f"Database Health     : {report['health']} %")

    print()
    print("=" * 55)


if __name__ == "__main__":
    main()
