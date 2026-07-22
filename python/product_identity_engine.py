#!/usr/bin/env python3
"""
Coupon World Product Intelligence Engine
Module 1: Product Identity Engine

Purpose:
- Read products from coupons.json
- Establish a reliable identity record for each product
- Normalize categories
- Extract safe identity signals from existing data
- Never fabricate missing product information
- Write results separately from the main product database

Default mode: DRY RUN
Write mode  : --write
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "coupons.json"
OUTPUT_DIR = ROOT / "data" / "intelligence"
OUTPUT_FILE = OUTPUT_DIR / "product_identity.json"
BACKUP_DIR = ROOT / ".identity_backups"


ASIN_PATTERN = re.compile(r"\b(B0[A-Z0-9]{8}|[A-Z0-9]{10})\b", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(20(?:1[5-9]|2[0-9]))\b")
RAM_PATTERN = re.compile(r"\b(\d{1,3})\s*GB\s*RAM\b", re.IGNORECASE)
STORAGE_PATTERN = re.compile(
    r"\b(\d{1,4})\s*(GB|TB)\s*(?:storage|ssd|rom)?\b",
    re.IGNORECASE,
)

KNOWN_BRANDS = {
    "amazon basics": "Amazon Basics",
    "american tourister": "American Tourister",
    "apple": "Apple",
    "asus": "ASUS",
    "bajaj": "Bajaj",
    "bausch lomb": "Bausch + Lomb",
    "boat": "boAt",
    "boult": "Boult",
    "campus": "Campus",
    "cello": "Cello",
    "dell": "Dell",
    "drivanto": "Drivanto",
    "ecovacs": "ECOVACS",
    "fire-boltt": "Fire-Boltt",
    "fire boltt": "Fire-Boltt",
    "gesto": "Gesto",
    "hauser": "Hauser",
    "hebezon": "Hebezon",
    "homestrap": "HomeStrap",
    "hp": "HP",
    "jbl": "JBL",
    "jiada": "Jiada",
    "kindle": "Kindle",
    "kore": "Kore",
    "lakme": "Lakmé",
    "levi's": "Levi's",
    "levis": "Levi's",
    "logitech": "Logitech",
    "mamaearth": "Mamaearth",
    "mi": "Mi",
    "milton": "Milton",
    "noise": "Noise",
    "nothing": "Nothing",
    "oneplus": "OnePlus",
    "philips": "Philips",
    "popsugar": "Popsugar",
    "prestige": "Prestige",
    "puma": "Puma",
    "realme": "realme",
    "redmi": "Redmi",
    "samsung": "Samsung",
    "sony": "Sony",
    "stempedia": "STEMpedia",
    "strauss": "Strauss",
    "tekcool": "Tekcool",
    "titan": "Titan",
    "typecase": "Typecase",
    "ugaoo": "Ugaoo",
    "wembley": "Wembley",
    "wildcraft": "Wildcraft",
    "yamaha": "Yamaha",
}

CATEGORY_RULES = {
    "mobile": "Mobiles",
    "mobiles": "Mobiles",
    "smartphone": "Mobiles",
    "smartphones": "Mobiles",
    "cell phones & accessories": "Mobiles",
    "electronics": "Electronics",
    "prime deal - electronics": "Electronics",
    "laptop": "Computers & Laptops",
    "laptops": "Computers & Laptops",
    "computer": "Computers & Laptops",
    "computers": "Computers & Laptops",
    "audio": "Audio",
    "headphones": "Audio",
    "earbuds": "Audio",
    "speakers": "Audio",
    "fashion": "Fashion",
    "clothing": "Fashion",
    "footwear": "Fashion",
    "beauty": "Beauty & Personal Care",
    "health & personal care": "Beauty & Personal Care",
    "home": "Home & Kitchen",
    "home & kitchen": "Home & Kitchen",
    "home improvement": "Home & Kitchen",
    "tools & hardware": "Tools & Hardware",
    "fitness": "Fitness",
    "sports": "Fitness",
    "toys": "Toys & Stationery",
    "prime deal - toys & stationery": "Toys & Stationery",
    "musical instruments": "Musical Instruments",
    "grocery": "Grocery",
    "appliances": "Appliances",
    "offers": "Offers",
}

SUBCATEGORY_KEYWORDS = (
    ("smartphone", ("smartphone", "iphone", "galaxy m", "redmi note", "nothing phone", "oneplus nord")),
    ("earbuds", ("earbuds", "airdopes", "buds", "tws")),
    ("headphones", ("headphone", "headset", "rockerz")),
    ("bluetooth speaker", ("bluetooth speaker", "speaker")),
    ("smartwatch", ("smartwatch", "smart watch", "colorfit")),
    ("laptop", ("laptop", "inspiron", "vivobook")),
    ("keyboard and mouse", ("keyboard", "mouse combo")),
    ("power bank", ("power bank", "powerbank")),
    ("microwave oven", ("microwave",)),
    ("induction cooktop", ("induction cooktop",)),
    ("water bottle", ("water bottle", "thermosteel", "bottle set")),
    ("trimmer", ("trimmer",)),
    ("running shoes", ("running shoes", "sneakers", "footwear")),
    ("t-shirt", ("t-shirt", "t shirt")),
    ("jeans", ("jeans",)),
    ("backpack", ("backpack",)),
    ("trolley bag", ("trolley", "luggage")),
    ("yoga mat", ("yoga mat",)),
    ("dumbbells", ("dumbbell",)),
    ("pull-up bar", ("pull-up bar", "pull up bar")),
    ("telescope", ("telescope",)),
    ("stationery", ("stationery", "gel pen", "notebook")),
    ("toy", ("toy", "hover football", "gesture control car")),
    ("plant", ("plant",)),
    ("ceiling fan", ("ceiling fan",)),
    ("air cooler", ("air cooler",)),
    ("gaming accessory", ("gaming",)),
)

COLOR_WORDS = (
    "black",
    "white",
    "blue",
    "red",
    "green",
    "grey",
    "gray",
    "silver",
    "gold",
    "pink",
    "purple",
    "orange",
    "yellow",
    "velvet black",
    "glacier blue",
    "hawaiian blue",
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def load_products() -> list[dict[str, Any]]:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

    data = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))

    if isinstance(data, list):
        products = data
    elif isinstance(data, dict) and isinstance(data.get("products"), list):
        products = data["products"]
    else:
        raise ValueError(
            "coupons.json must contain a product list or a {'products': [...]} object."
        )

    return [item for item in products if isinstance(item, dict)]


def extract_asin(product: dict[str, Any]) -> tuple[str | None, list[str]]:
    evidence: list[str] = []

    existing = clean_text(product.get("asin")).upper()
    if ASIN_PATTERN.fullmatch(existing):
        evidence.append("existing asin field")
        return existing, evidence

    link = clean_text(product.get("link"))
    if link:
        parsed = urlparse(link)

        query_asin = parse_qs(parsed.query).get("asin", [])
        if query_asin:
            candidate = clean_text(query_asin[0]).upper()
            if ASIN_PATTERN.fullmatch(candidate):
                evidence.append("asin query parameter")
                return candidate, evidence

        path_patterns = (
            r"/dp/([A-Z0-9]{10})(?:[/?]|$)",
            r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)",
            r"/product/([A-Z0-9]{10})(?:[/?]|$)",
        )

        for pattern in path_patterns:
            match = re.search(pattern, parsed.path, re.IGNORECASE)
            if match:
                evidence.append("retailer URL path")
                return match.group(1).upper(), evidence

    title = clean_text(product.get("title"))
    match = ASIN_PATTERN.search(title)
    if match and match.group(1).upper().startswith("B0"):
        evidence.append("title identifier")
        return match.group(1).upper(), evidence

    return None, evidence


def detect_brand(product: dict[str, Any]) -> tuple[str | None, list[str]]:
    evidence: list[str] = []

    existing = clean_text(product.get("brand"))
    if existing:
        evidence.append("existing brand field")
        return existing, evidence

    title = clean_text(product.get("title"))
    normalized_title = title.lower()

    for key in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", normalized_title):
            evidence.append("brand matched from title")
            return KNOWN_BRANDS[key], evidence

    return None, evidence


def normalize_category(product: dict[str, Any]) -> tuple[str, list[str]]:
    evidence: list[str] = []

    raw_category = clean_text(product.get("category"))
    key = raw_category.lower()

    if key in CATEGORY_RULES:
        evidence.append("existing category normalized")
        return CATEGORY_RULES[key], evidence

    title = clean_text(product.get("title")).lower()

    category_keywords = (
        ("Mobiles", ("smartphone", "iphone", "mobile phone", "galaxy m", "redmi note", "nothing phone")),
        ("Computers & Laptops", ("laptop", "keyboard", "mouse", "ssd")),
        ("Audio", ("earbuds", "headphone", "headset", "speaker", "airdopes", "buds")),
        ("Electronics", ("smartwatch", "power bank", "fire tv", "kindle")),
        ("Fashion", ("t-shirt", "jeans", "shoes", "sneakers", "watch", "backpack", "trolley")),
        ("Beauty & Personal Care", ("makeup", "skincare", "trimmer", "contact lens")),
        ("Home & Kitchen", ("bottle", "storage organizer", "plant", "chair bush")),
        ("Appliances", ("microwave", "induction", "fan", "air cooler", "washing machine")),
        ("Fitness", ("dumbbell", "yoga mat", "pull-up bar", "pull up bar")),
        ("Toys & Stationery", ("toy", "stationery", "gel pen", "construction kit")),
        ("Musical Instruments", ("keyboard 37 keys", "musical keyboard")),
        ("Tools & Hardware", ("electric drill", "angle grinder", "tools")),
    )

    for category, keywords in category_keywords:
        if any(keyword in title for keyword in keywords):
            evidence.append("category inferred from title keywords")
            return category, evidence

    if raw_category:
        evidence.append("existing category retained without normalization")
        return raw_category, evidence

    return "Unclassified", evidence


def detect_subcategory(title: str) -> tuple[str | None, list[str]]:
    normalized = title.lower()

    for subcategory, keywords in SUBCATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return subcategory, ["subcategory inferred from title keywords"]

    return None, []


def extract_launch_year(product: dict[str, Any]) -> tuple[int | None, list[str]]:
    existing = product.get("launch_year")

    if isinstance(existing, int) and 2015 <= existing <= 2029:
        return existing, ["existing launch_year field"]

    title = clean_text(product.get("title"))
    matches = YEAR_PATTERN.findall(title)

    if matches:
        return int(matches[-1]), ["launch year found in title"]

    return None, []


def extract_variant(title: str) -> tuple[dict[str, Any], list[str]]:
    variant: dict[str, Any] = {
        "ram": None,
        "storage": None,
        "color": None,
    }
    evidence: list[str] = []

    ram_match = RAM_PATTERN.search(title)
    if ram_match:
        variant["ram"] = f"{ram_match.group(1)} GB"
        evidence.append("RAM extracted from title")

    storage_candidates = STORAGE_PATTERN.findall(title)
    if storage_candidates:
        values = [
            f"{amount.upper()} {unit.upper()}"
            for amount, unit in storage_candidates
        ]

        ram_value = variant["ram"]
        for value in values:
            if ram_value and value == ram_value:
                continue
            variant["storage"] = value
            evidence.append("storage extracted from title")
            break

    normalized_title = title.lower()
    for color in sorted(COLOR_WORDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(color)}\b", normalized_title):
            variant["color"] = color.title()
            evidence.append("color extracted from title")
            break

    return variant, evidence


def detect_model(
    product: dict[str, Any],
    brand: str | None,
) -> tuple[str | None, list[str]]:
    existing = clean_text(product.get("model"))

    if existing:
        return existing, ["existing model field"]

    # Deliberately conservative:
    # A title is not automatically treated as a model number.
    return None, []


def identity_confidence(
    asin: str | None,
    brand: str | None,
    category: str,
    subcategory: str | None,
    model: str | None,
    title: str,
) -> tuple[int, str]:
    score = 0

    if title:
        score += 20
    if asin:
        score += 25
    if brand:
        score += 20
    if category and category != "Unclassified":
        score += 20
    if subcategory:
        score += 10
    if model:
        score += 5

    score = min(score, 100)

    if score >= 85:
        level = "high"
    elif score >= 60:
        level = "medium"
    else:
        level = "low"

    return score, level
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def canonical_product_id(
    brand: str | None,
    title: str,
    model: str | None,
    variant: dict[str, Any],
) -> str:
    base_text = model or title

    if brand:
        base_text = re.sub(
            rf"(?<![a-z0-9]){re.escape(brand)}(?![a-z0-9])",
            " ",
            base_text,
            flags=re.IGNORECASE,
        )

    for value in (variant.get("storage"), variant.get("color")):
        if value:
            base_text = re.sub(
                rf"(?<![a-z0-9]){re.escape(str(value))}(?![a-z0-9])",
                " ",
                base_text,
                flags=re.IGNORECASE,
            )

    parts = []

    if brand:
        parts.append(brand)

    parts.append(base_text)

    if variant.get("storage"):
        parts.append(str(variant["storage"]))

    if variant.get("color"):
        parts.append(str(variant["color"]))

    return slugify(" ".join(parts))
    

def product_identifier(product: dict[str, Any], index: int) -> str:
    for field in ("id", "sl_no", "asin"):
        value = clean_text(product.get(field))
        if value:
            return value

    return str(index)


def build_identity(product: dict[str, Any], index: int) -> dict[str, Any]:
    title = clean_text(product.get("title"))

    asin, asin_evidence = extract_asin(product)
    brand, brand_evidence = detect_brand(product)
    category, category_evidence = normalize_category(product)
    subcategory, subcategory_evidence = detect_subcategory(title)
    launch_year, year_evidence = extract_launch_year(product)
    variant, variant_evidence = extract_variant(title)
    model, model_evidence = detect_model(product, brand)

    warnings: list[str] = []

    if not title:
        warnings.append("missing title")
    if not asin:
        warnings.append("asin unavailable")
    if not brand:
        warnings.append("brand unavailable")
    if category == "Unclassified":
        warnings.append("category unclassified")
    if not subcategory:
        warnings.append("subcategory unavailable")
    if not model:
        warnings.append("model not explicitly available")

    score, level = identity_confidence(
        asin=asin,
        brand=brand,
        category=category,
        subcategory=subcategory,
        model=model,
        title=title,
    )

    source_category = clean_text(product.get("category")) or None
    source_link = clean_text(product.get("link")) or None

    return {
        "product_id": product_identifier(product, index),
                "canonical_id": canonical_product_id(
            brand=brand,
            title=title,
            model=model,
            variant=variant,
        ),
        "source_index": index,
        "title": title or None,
        "normalized_title": title.casefold() if title else None,
        "asin": asin,
        "brand": brand,
        "model": model,
        "category": category,
        "source_category": source_category,
        "subcategory": subcategory,
        "variant": variant,
        "launch_year": launch_year,
        "source_link": source_link,
        "identity_confidence": {
            "score": score,
            "level": level,
        },
        "evidence": list(
            dict.fromkeys(
                asin_evidence
                + brand_evidence
                + category_evidence
                + subcategory_evidence
                + model_evidence
                + year_evidence
                + variant_evidence
            )
        ),
        "warnings": warnings,
    }


def create_payload(identities: list[dict[str, Any]]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()

    confidence_counts = Counter(
        item["identity_confidence"]["level"] for item in identities
    )
    category_counts = Counter(item["category"] for item in identities)

    return {
        "engine": {
            "name": "Coupon World Product Identity Engine",
            "module": 1,
            "version": "1.0.0",
            "generated_at": generated_at,
            "source_file": SOURCE_FILE.name,
            "fabricated_fields_allowed": False,
        },
        "summary": {
            "total_products": len(identities),
            "with_asin": sum(bool(item["asin"]) for item in identities),
            "with_brand": sum(bool(item["brand"]) for item in identities),
            "with_subcategory": sum(bool(item["subcategory"]) for item in identities),
            "with_model": sum(bool(item["model"]) for item in identities),
            "unclassified": sum(
                item["category"] == "Unclassified" for item in identities
            ),
            "confidence": dict(sorted(confidence_counts.items())),
            "categories": dict(sorted(category_counts.items())),
        },
        "products": identities,
    }


def write_output(payload: dict[str, Any]) -> Path | None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None

    if OUTPUT_FILE.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_DIR / f"product_identity-{timestamp}.json"
        shutil.copy2(OUTPUT_FILE, backup_path)

    temporary_file = OUTPUT_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_file.replace(OUTPUT_FILE)

    return backup_path


def print_report(payload: dict[str, Any], write_mode: bool) -> None:
    summary = payload["summary"]

    print()
    print("=" * 62)
    print("COUPON WORLD PRODUCT IDENTITY ENGINE — MODULE 1")
    print("=" * 62)
    print(f"Source file          : {SOURCE_FILE.name}")
    print(f"Products processed   : {summary['total_products']}")
    print(f"Products with ASIN   : {summary['with_asin']}")
    print(f"Products with brand  : {summary['with_brand']}")
    print(f"With subcategory     : {summary['with_subcategory']}")
    print(f"With explicit model  : {summary['with_model']}")
    print(f"Unclassified         : {summary['unclassified']}")
    print(f"Write mode           : {'YES' if write_mode else 'NO — DRY RUN'}")
    print(f"Output file          : {OUTPUT_FILE.relative_to(ROOT)}")
    print("-" * 62)

    confidence = summary["confidence"]

    print(
        "Confidence           : "
        f"High {confidence.get('high', 0)} | "
        f"Medium {confidence.get('medium', 0)} | "
        f"Low {confidence.get('low', 0)}"
    )

    print("-" * 62)
    print("CATEGORY DISTRIBUTION")

    for category, count in summary["categories"].items():
        print(f"  {category:<28} {count}")

    print("=" * 62)

    if not write_mode:
        print("DRY RUN COMPLETE")
        print("No files were changed.")
        print()
        print("To generate the identity database, run:")
        print("python python/product_identity_engine.py --write")
    else:
        print("PRODUCT IDENTITY DATABASE GENERATED")
        print(f"Saved to: {OUTPUT_FILE.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Coupon World product identity database."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write data/intelligence/product_identity.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products = load_products()
        identities = [
            build_identity(product, index)
            for index, product in enumerate(products, start=1)
        ]
        payload = create_payload(identities)

        if args.write:
            backup_path = write_output(payload)
            if backup_path:
                print(
                    f"Existing identity database backed up to: "
                    f"{backup_path.relative_to(ROOT)}"
                )

        print_report(payload, write_mode=args.write)
        return 0

    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
