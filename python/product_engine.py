#!/usr/bin/env python3
"""
Coupon World AI OS
Product Engine v1.2

Features:
- Validates coupons.json
- Detects missing brands from product titles
- Generates safe factual descriptions
- Supports dry-run preview
- Creates a timestamped backup before writing
- Never invents prices, discounts, ratings, reviews, stock, or urgency
"""

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


KNOWN_BRANDS = {
    "boat": "boAt",
    "apple": "Apple",
    "samsung": "Samsung",
    "redmi": "Redmi",
    "realme": "realme",
    "noise": "Noise",
    "fire-boltt": "Fire-Boltt",
    "fire boltt": "Fire-Boltt",
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
    "amazon": "Amazon",
    "ecovacs": "ECOVACS",
    "yamaha": "Yamaha",
    "logitech": "Logitech",
    "amway": "Amway",
    "nutrilite": "Nutrilite",
    "philips": "Philips",
    "havells": "Havells",
    "bajaj": "Bajaj",
    "prestige": "Prestige",
    "pigeon": "Pigeon",
    "agaro": "AGARO",
    "mi ": "Mi",
    "motorola": "Motorola",
    "moto ": "Motorola",
    "iqoo": "iQOO",
    "nothing": "Nothing",
    "portronics": "Portronics",
    "zebronics": "Zebronics",
    "wipro": "Wipro",
    "syska": "Syska",
    "crocs": "Crocs",
    "puma": "Puma",
    "adidas": "Adidas",
    "nike": "Nike",
    "campus": "Campus",
    "skechers": "Skechers",
    "fastrack": "Fastrack",
    "titan": "Titan",
    "casio": "Casio",
    "wildcraft": "Wildcraft",
    "american tourister": "American Tourister",
    "hauser": "Hauser",
    "wembley": "Wembley",
    "encasify": "Encasify",
    "stempedia": "STEMpedia",
    "ssea": "SSEA",
    "jiada": "JIADA",
    "teeslix": "TeeSlix",
    "bausch + lomb": "Bausch + Lomb",
    "aasons": "AASONS",
    "hebezon": "Hebezon",
    "homestrap": "HomeStrap",
    "audavibe": "Audavibe",
    "gesto": "Gesto",
    "popsugar": "Popsugar",
    "tekcool": "TEKCOOL",
    "echo dot": "Amazon",
    "milton": "Milton",
    "boult audio": "Boult Audio",
    "fire tv": "Amazon",
    "kindle": "Amazon",
    "levi's": "Levi's",
    "strauss": "Strauss",
    "mamaearth": "Mamaearth",
    "kore": "Kore",
    "cello": "Cello",
    "drivanto": "Drivanto",
    "ugaoo": "UGAOO",
    "lakme": "Lakme",
    "qubo": "Qubo",
    "cp plus": "CP PLUS",
    "countrycam": "COUNTRYCAM",
    "trueview": "Trueview",
    "manomay": "MANOMAY"
}


ROOT = Path(__file__).resolve().parent.parent
COUPONS_FILE = ROOT / "coupons.json"
BACKUP_DIR = ROOT / "backups"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and improve Coupon World product data."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write detected brands and generated descriptions to coupons.json.",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=10,
        help="Maximum number of proposed changes shown in dry-run mode.",
    )
    return parser.parse_args()


def load_json(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(f"Product database not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list of products.")

    products: list[dict[str, Any]] = []

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Product number {index} is invalid. Every product must be an object."
            )
        products.append(item)

    return products


def save_json(file_path: Path, products: list[dict[str, Any]]) -> None:
    temporary_file = file_path.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)
        file.write("\n")

    temporary_file.replace(file_path)


def create_backup(file_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = BACKUP_DIR / f"coupons-{timestamp}.json"

    shutil.copy2(file_path, backup_file)
    return backup_file


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def detect_brand(title: Any) -> str:
    normalized_title = clean_text(title).casefold()

    if not normalized_title:
        return ""

    for keyword, brand in sorted(
        KNOWN_BRANDS.items(),
        key=lambda item: len(item[0].strip()),
        reverse=True,
    ):
        normalized_keyword = keyword.casefold().strip()

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_keyword)
            + r"(?![a-z0-9])"
        )

        match = re.search(pattern, normalized_title)

        if not match:
            continue

        prefix = normalized_title[max(0, match.start() - 30):match.start()]

        compatibility_phrases = (
            "for ",
            "compatible with ",
            "case for ",
            "cover for ",
            "designed for ",
            "suitable for ",
        )

        if any(prefix.endswith(phrase) for phrase in compatibility_phrases):
            continue

        return brand

    return ""


def generate_description(product: dict[str, Any], brand: str) -> str:
    title = clean_text(product.get("title"))
    category = clean_text(product.get("category"))
    store = clean_text(product.get("store"))

    if not title:
        return ""

    parts = [title]

    article = "an" if brand and brand[0].casefold() in "aeiou" else "a"

    if brand and category:
        parts.append(
            f"is {article} {brand} product listed in the {category} category on Coupon World."
        )
    elif brand:
        parts.append(
            f"is {article} {brand} product listed on Coupon World."
        )
    elif category:
        parts.append(
            f"is listed in the {category} category on Coupon World."
        )
    else:
        parts.append("is listed on Coupon World.")

    if store:
        parts.append(
            f"Visit the {store} product page to check the latest price, "
            "availability and offer details."
        )
    else:
        parts.append(
            "Open the product page to check the latest price, "
            "availability and offer details."
        )

    return " ".join(parts)


def improve_products(
    products: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []

    for index, product in enumerate(products, start=1):
        product_changes: dict[str, str] = {}

        existing_brand = clean_text(product.get("brand"))
        detected_brand = existing_brand or detect_brand(product.get("title"))

        if not existing_brand and detected_brand:
            product["brand"] = detected_brand
            product_changes["brand"] = detected_brand

        existing_description = clean_text(product.get("description"))

        if not existing_description:
            description = generate_description(product, detected_brand)

            if description:
                product["description"] = description
                product_changes["description"] = description

        if product_changes:
            changes.append(
                {
                    "index": index,
                    "id": product.get("id") or product.get("sl_no", ""),
                    "title": clean_text(product.get("title")),
                    "changes": product_changes,
                }
            )

    return products, changes


def calculate_health(report: dict[str, int]) -> int:
    if report["products"] == 0:
        return 0

    total_checks = report["products"] * 5

    failed_checks = (
        report["missing_brand"]
        + report["missing_category"]
        + report["missing_image"]
        + report["missing_description"]
        + report["missing_link"]
    )

    return max(0, round((1 - failed_checks / total_checks) * 100))


def validate_products(products: list[dict[str, Any]]) -> dict[str, int]:
    report = {
        "products": len(products),
        "complete": 0,
        "incomplete": 0,
        "missing_brand": 0,
        "missing_category": 0,
        "missing_image": 0,
        "missing_description": 0,
        "missing_link": 0,
        "health": 0,
    }

    for product in products:
        complete = True

        brand = clean_text(product.get("brand")) or detect_brand(
            product.get("title")
        )

        if not brand:
            report["missing_brand"] += 1
            complete = False

        if not clean_text(product.get("category")):
            report["missing_category"] += 1
            complete = False

        if not clean_text(product.get("image")):
            report["missing_image"] += 1
            complete = False

        if not clean_text(product.get("description")):
            report["missing_description"] += 1
            complete = False

        if not clean_text(product.get("link")):
            report["missing_link"] += 1
            complete = False

        if complete:
            report["complete"] += 1
        else:
            report["incomplete"] += 1

    report["health"] = calculate_health(report)
    return report


def print_report(title: str, report: dict[str, int]) -> None:
    print()
    print(title)
    print("-" * 55)
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


def print_preview(
    changes: list[dict[str, Any]],
    preview_limit: int,
) -> None:
    print()
    print("Proposed Changes")
    print("-" * 55)

    if not changes:
        print("No brand or description changes are required.")
        return

    safe_limit = max(0, preview_limit)

    for change in changes[:safe_limit]:
        identity = change["id"] or change["index"]

        print()
        print(f"Product {identity}: {change['title'][:90]}")

        if "brand" in change["changes"]:
            print(f"  Brand       : {change['changes']['brand']}")

        if "description" in change["changes"]:
            print(
                f"  Description : "
                f"{change['changes']['description'][:180]}"
            )

    remaining = len(changes) - safe_limit

    if remaining > 0:
        print()
        print(f"...and {remaining} more product changes.")


def main() -> int:
    args = parse_arguments()

    print("=" * 55)
    print("Coupon World AI OS")
    print("Product Engine v1.2")
    print("=" * 55)

    try:
        products = load_json(COUPONS_FILE)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print()
        print(f"ERROR: {error}")
        return 1

    original_report = validate_products(products)
    print_report("Current Database", original_report)

    improved_products, changes = improve_products(products)
    improved_report = validate_products(improved_products)

    print_preview(changes, args.preview_limit)
    print_report("Expected Database After Update", improved_report)

    print()
    print(f"Products Changed    : {len(changes)}")

    if not changes:
        print("No update was required.")
        print("=" * 55)
        return 0

    if not args.write:
        print()
        print("DRY RUN ONLY: coupons.json has not been changed.")
        print("Run with --write after reviewing the preview.")
        print("=" * 55)
        return 0

    try:
        backup_file = create_backup(COUPONS_FILE)
        save_json(COUPONS_FILE, improved_products)
    except OSError as error:
        print()
        print(f"ERROR: Unable to update database: {error}")
        return 1

    print()
    print(f"Backup Created      : {backup_file.relative_to(ROOT)}")
    print(f"Database Updated    : {COUPONS_FILE.name}")
    print("=" * 55)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
