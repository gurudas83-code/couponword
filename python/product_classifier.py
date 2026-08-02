#!/usr/bin/env python3
"""
Coupon World Product Classifier v1.1

Creates a reviewable product taxonomy for coupons.json.

Input
-----
coupons.json

Output
------
data/intelligence/product_taxonomy.json

Design
------
- Read-only: coupons.json is never modified.
- Deterministic: no paid AI/API required.
- Product type is inferred from title, brand, model and current category.
- Ambiguous products remain manual_review instead of being guessed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DB = ROOT / "coupons.json"
OUTPUT_DB = ROOT / "data" / "intelligence" / "product_taxonomy.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+\s.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(f"{path.name} must use UTF-8 encoding") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path.name}: {error}") from error


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_product_id(product: dict[str, Any], position: int) -> str:
    value = (
        product.get("id")
        or product.get("product_id")
        or product.get("sl_no")
        or product.get("asin")
        or position
    )
    return str(value)


def phrase_match(text: str, phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


# Higher priority rules must come first.
RULES: tuple[dict[str, Any], ...] = (
    {
        "product_type": "tablet_keyboard_case",
        "shopping_category": "Computer & Mobile Accessories",
        "parent_category": "Electronics",
        "phrases": (
            "keyboard case",
            "folio cover",
            "detachable bluetooth keyboard",
            "tablet keyboard",
        ),
        "tags": ("keyboard", "tablet accessory", "case", "bluetooth"),
        "buyer_intents": ("tablet productivity", "portable typing"),
    },
    {
        "product_type": "musical_keyboard",
        "shopping_category": "Musical Instruments",
        "parent_category": "Hobbies & Entertainment",
        "phrases": (
            "portable mini keyboard",
            "portable keyboard",
            "electronic keyboard",
            "musical keyboard",
            "pss-e30",
            "37 keys",
            "61 keys",
        ),
        "tags": ("keyboard instrument", "music", "keys"),
        "buyer_intents": ("music learning", "kids music"),
    },
    {
        "product_type": "smartphone",
        "shopping_category": "Smartphones",
        "parent_category": "Electronics",
        "phrases": (
            "iphone",
            "redmi note",
            "redmi 13",
            "samsung galaxy",
            "oneplus nord",
            "nothing phone",
            "mobile phone",
            "smartphone",
            "galaxy m",
        ),
        "tags": ("mobile", "phone", "smartphone"),
        "buyer_intents": ("daily use", "communication"),
    },
    {
        "product_type": "earbuds",
        "shopping_category": "Audio",
        "parent_category": "Electronics",
        "phrases": (
            "earbuds",
            "ear buds",
            "airdopes",
            "airpods",
            "buds t",
            "buds air",
            "tws",
            "true wireless",
        ),
        "tags": ("audio", "earbuds", "wireless"),
        "buyer_intents": ("music", "calling", "travel"),
    },
    {
        "product_type": "headphones",
        "shopping_category": "Audio",
        "parent_category": "Electronics",
        "phrases": (
            "headphones",
            "headphone",
            "headset",
            "rockerz",
            "wired headset",
        ),
        "tags": ("audio", "headphones"),
        "buyer_intents": ("music", "calling", "gaming"),
    },
    {
        "product_type": "bluetooth_speaker",
        "shopping_category": "Audio",
        "parent_category": "Electronics",
        "phrases": (
            "bluetooth speaker",
            "boat stone",
            "portable speaker",
        ),
        "tags": ("speaker", "bluetooth", "audio"),
        "buyer_intents": ("music", "party", "portable audio"),
    },
    {
        "product_type": "computer_keyboard",
        "shopping_category": "Computer Accessories",
        "parent_category": "Electronics",
        "phrases": (
            "wireless keyboard",
            "mechanical keyboard",
            "gaming keyboard",
            "keyboard and mouse combo",
            "keyboard mouse combo",
            "mk240",
        ),
        "tags": ("keyboard", "computer accessory"),
        "buyer_intents": ("office productivity", "typing"),
    },
    {
        "product_type": "computer_mouse",
        "shopping_category": "Computer Accessories",
        "parent_category": "Electronics",
        "phrases": (
            "wireless mouse",
            "gaming mouse",
            "bluetooth mouse",
        ),
        "tags": ("mouse", "computer accessory"),
        "buyer_intents": ("office productivity", "computer use"),
    },
    {
        "product_type": "laptop",
        "shopping_category": "Laptops",
        "parent_category": "Electronics",
        "phrases": (
            "gaming laptop",
            "inspiron laptop",
            "notebook computer",
            "laptop",
        ),
        "tags": ("laptop", "computer"),
        "buyer_intents": ("work", "study", "gaming"),
    },
    {
        "product_type": "smartwatch",
        "shopping_category": "Wearables",
        "parent_category": "Electronics",
        "phrases": (
            "smartwatch",
            "smart watch",
            "colorfit",
            "bluetooth calling watch",
        ),
        "tags": ("smartwatch", "wearable"),
        "buyer_intents": ("fitness tracking", "notifications"),
    },
    {
        "product_type": "analog_watch",
        "shopping_category": "Watches",
        "parent_category": "Fashion",
        "phrases": (
            "analog watch",
            "wrist watch",
        ),
        "tags": ("watch", "fashion accessory"),
        "buyer_intents": ("daily wear", "gifting"),
    },
    {
        "product_type": "memory_card",
        "shopping_category": "Storage",
        "parent_category": "Electronics",
        "phrases": (
            "micro sd",
            "microsd",
            "memory card",
            "sd card",
        ),
        "tags": ("storage", "memory card"),
        "buyer_intents": ("device storage",),
    },
    {
        "product_type": "power_bank",
        "shopping_category": "Mobile Accessories",
        "parent_category": "Electronics",
        "phrases": (
            "power bank",
            "powerbank",
        ),
        "tags": ("charging", "power bank", "mobile accessory"),
        "buyer_intents": ("travel charging", "backup power"),
    },
    {
        "product_type": "streaming_device",
        "shopping_category": "TV & Streaming",
        "parent_category": "Electronics",
        "phrases": (
            "fire tv stick",
            "streaming stick",
            "chromecast",
        ),
        "tags": ("streaming", "tv accessory"),
        "buyer_intents": ("home entertainment",),
    },
    {
        "product_type": "smart_speaker",
        "shopping_category": "Smart Home",
        "parent_category": "Electronics",
        "phrases": (
            "echo dot",
            "smart speaker",
            "alexa speaker",
        ),
        "tags": ("smart speaker", "voice assistant"),
        "buyer_intents": ("smart home", "music"),
    },
    {
        "product_type": "e_reader",
        "shopping_category": "E-Readers",
        "parent_category": "Electronics",
        "phrases": (
            "kindle",
            "e reader",
            "ereader",
        ),
        "tags": ("reading", "e-reader"),
        "buyer_intents": ("digital reading",),
    },
    {
        "product_type": "telescope",
        "shopping_category": "Optics & Astronomy",
        "parent_category": "Hobbies & Entertainment",
        "phrases": (
            "telescope 235x",
            "reflector telescope",
            "astronomical telescope",
            "telescope for moon",
        ),
        "tags": ("telescope", "astronomy"),
        "buyer_intents": ("astronomy", "hobby"),
    },
    {
        "product_type": "telescope_cover",
        "shopping_category": "Optics Accessories",
        "parent_category": "Hobbies & Entertainment",
        "phrases": (
            "telescope cover",
        ),
        "tags": ("telescope accessory", "protective cover"),
        "buyer_intents": ("equipment protection",),
    },
    {
        "product_type": "projector_lamp",
        "shopping_category": "Decorative Lighting",
        "parent_category": "Home",
        "phrases": (
            "galaxy projector",
            "planetarium",
            "nebula moon lamp",
        ),
        "tags": ("projector lamp", "decor", "lighting"),
        "buyer_intents": ("room decor", "gifting"),
    },
    {
        "product_type": "air_cooler",
        "shopping_category": "Cooling Appliances",
        "parent_category": "Home Appliances",
        "phrases": (
            "air cooler",
            "cooling fan",
            "mini cooling fan",
        ),
        "tags": ("cooling", "fan"),
        "buyer_intents": ("personal cooling",),
    },
    {
        "product_type": "ceiling_fan",
        "shopping_category": "Fans",
        "parent_category": "Home Appliances",
        "phrases": (
            "ceiling fan",
        ),
        "tags": ("fan", "home appliance"),
        "buyer_intents": ("home cooling",),
    },
    {
        "product_type": "microwave_oven",
        "shopping_category": "Kitchen Appliances",
        "parent_category": "Home Appliances",
        "phrases": (
            "microwave oven",
            "microwave",
        ),
        "tags": ("microwave", "kitchen appliance"),
        "buyer_intents": ("cooking", "reheating"),
    },
    {
        "product_type": "induction_cooktop",
        "shopping_category": "Kitchen Appliances",
        "parent_category": "Home Appliances",
        "phrases": (
            "induction cooktop",
            "induction stove",
        ),
        "tags": ("induction", "cooktop"),
        "buyer_intents": ("cooking",),
    },
    {
        "product_type": "water_bottle",
        "shopping_category": "Drinkware",
        "parent_category": "Home & Kitchen",
        "phrases": (
            "thermosteel bottle",
            "water bottle set",
            "water bottle",
            "flask bottle",
        ),
        "tags": ("bottle", "drinkware"),
        "buyer_intents": ("hydration", "travel"),
    },
    {
        "product_type": "appliance_stand",
        "shopping_category": "Appliance Accessories",
        "parent_category": "Home Improvement",
        "phrases": (
            "washing machine stand",
            "appliance roller stand",
            "mobile dolly",
            "adjustable moving base",
            "movable adjustable base",
        ),
        "tags": ("appliance stand", "wheels", "home utility"),
        "buyer_intents": ("appliance mobility", "floor protection"),
    },
    {
        "product_type": "storage_organizer",
        "shopping_category": "Home Storage",
        "parent_category": "Home & Kitchen",
        "phrases": (
            "storage organizer",
            "storage organisers",
            "storage basket",
            "plastic storage",
        ),
        "tags": ("storage", "organizer"),
        "buyer_intents": ("home organization",),
    },
    {
        "product_type": "indoor_plants",
        "shopping_category": "Plants & Gardening",
        "parent_category": "Home & Garden",
        "phrases": (
            "indoor plants",
            "money plant",
            "jade plant",
            "peace lily",
        ),
        "tags": ("plants", "home decor"),
        "buyer_intents": ("home decor", "gardening"),
    },
    {
        "product_type": "trimmer",
        "shopping_category": "Grooming",
        "parent_category": "Beauty & Personal Care",
        "phrases": (
            "trimmer",
            "beard trimmer",
            "hair trimmer",
        ),
        "tags": ("grooming", "trimmer"),
        "buyer_intents": ("personal grooming",),
    },
    {
        "product_type": "contact_lens_solution",
        "shopping_category": "Eye Care",
        "parent_category": "Health & Personal Care",
        "phrases": (
            "contact lens solution",
            "multi-purpose 500ml contact lens",
        ),
        "tags": ("eye care", "contact lens"),
        "buyer_intents": ("lens cleaning",),
    },
    {
        "product_type": "nutrition_supplement",
        "shopping_category": "Nutrition",
        "parent_category": "Health & Personal Care",
        "phrases": (
            "nutrilite",
            "cal mag",
            "tablets",
            "supplement",
        ),
        "tags": ("nutrition", "supplement"),
        "buyer_intents": ("daily nutrition",),
    },
    {
        "product_type": "skincare_set",
        "shopping_category": "Skin Care",
        "parent_category": "Beauty",
        "phrases": (
            "skincare combo",
            "skin care combo",
        ),
        "tags": ("skincare", "beauty"),
        "buyer_intents": ("skin care", "gifting"),
    },
    {
        "product_type": "makeup_kit",
        "shopping_category": "Makeup",
        "parent_category": "Beauty",
        "phrases": (
            "makeup kit",
            "cosmetic kit",
        ),
        "tags": ("makeup", "beauty"),
        "buyer_intents": ("makeup", "gifting"),
    },
    {
        "product_type": "running_shoes",
        "shopping_category": "Footwear",
        "parent_category": "Fashion",
        "phrases": (
            "running shoes",
            "sneakers",
            "sports shoes",
        ),
        "tags": ("shoes", "footwear"),
        "buyer_intents": ("running", "daily wear"),
    },
    {
        "product_type": "clothing",
        "shopping_category": "Clothing",
        "parent_category": "Fashion",
        "phrases": (
            "t-shirt",
            "t shirt",
            "jeans",
            "shirt",
            "dress",
            "kurta",
        ),
        "tags": ("clothing", "fashion"),
        "buyer_intents": ("daily wear",),
    },
    {
        "product_type": "trolley_bag",
        "shopping_category": "Luggage",
        "parent_category": "Fashion & Travel",
        "phrases": (
            "trolley bag",
            "suitcase",
            "luggage",
        ),
        "tags": ("luggage", "travel"),
        "buyer_intents": ("travel",),
    },
    {
        "product_type": "backpack",
        "shopping_category": "Bags",
        "parent_category": "Fashion & Travel",
        "phrases": (
            "backpack",
            "school bag",
        ),
        "tags": ("bag", "backpack"),
        "buyer_intents": ("travel", "school", "office"),
    },
    {
        "product_type": "yoga_mat",
        "shopping_category": "Yoga",
        "parent_category": "Fitness",
        "phrases": (
            "yoga mat",
            "exercise mat",
        ),
        "tags": ("fitness", "yoga"),
        "buyer_intents": ("yoga", "exercise"),
    },
    {
        "product_type": "dumbbells",
        "shopping_category": "Strength Training",
        "parent_category": "Fitness",
        "phrases": (
            "dumbbells",
            "adjustable dumbbell",
        ),
        "tags": ("fitness", "weights"),
        "buyer_intents": ("strength training", "home workout"),
    },
    {
        "product_type": "pull_up_bar",
        "shopping_category": "Strength Training",
        "parent_category": "Fitness",
        "phrases": (
            "pull-up bar",
            "pull up bar",
            "doorway pull",
        ),
        "tags": ("fitness", "pull-up bar"),
        "buyer_intents": ("strength training", "home workout"),
    },
    {
        "product_type": "construction_toy",
        "shopping_category": "Educational Toys",
        "parent_category": "Toys",
        "phrases": (
            "mechanical construction kit",
            "stem kit",
            "construction kit",
        ),
        "tags": ("toy", "stem", "educational"),
        "buyer_intents": ("learning", "gifting"),
    },
    {
        "product_type": "remote_control_toy",
        "shopping_category": "Remote Control Toys",
        "parent_category": "Toys",
        "phrases": (
            "gesture control car",
            "rc stunt car",
            "remote control car",
        ),
        "tags": ("toy", "remote control"),
        "buyer_intents": ("kids play", "gifting"),
    },
    {
        "product_type": "indoor_game",
        "shopping_category": "Indoor Games",
        "parent_category": "Toys",
        "phrases": (
            "hover football",
            "floating soccer ball",
        ),
        "tags": ("toy", "indoor game"),
        "buyer_intents": ("kids play", "gifting"),
    },
    {
        "product_type": "stationery_set",
        "shopping_category": "Stationery",
        "parent_category": "Office & School Supplies",
        "phrases": (
            "stationery set",
            "notebook and pen",
            "return gift",
        ),
        "tags": ("stationery", "gift"),
        "buyer_intents": ("school", "gifting"),
    },
    {
        "product_type": "gel_pens",
        "shopping_category": "Writing Supplies",
        "parent_category": "Office & School Supplies",
        "phrases": (
            "gel pen",
            "pens",
            "pen jar",
        ),
        "tags": ("pen", "stationery"),
        "buyer_intents": ("writing", "school", "office"),
    },
    {
        "product_type": "power_tool_accessory",
        "shopping_category": "Tools",
        "parent_category": "Home Improvement",
        "phrases": (
            "angle grinder connecting rod",
            "cutting blade",
            "grinding wheel",
            "electric drill",
        ),
        "tags": ("tool", "drill", "grinder"),
        "buyer_intents": ("repair", "diy"),
    },
    {
        "product_type": "furniture_hardware",
        "shopping_category": "Furniture Hardware",
        "parent_category": "Industrial & Hardware",
        "phrases": (
            "chair bush",
            "furniture bush",
        ),
        "tags": ("hardware", "furniture repair"),
        "buyer_intents": ("repair",),
    },
)


PROMOTIONAL_PHRASES = (
    "mega 70",
    "off store",
    "fashion fest",
    "online store",
    "offers",
)


FEATURE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("wireless", ("wireless", "bluetooth", "tws")),
    ("bluetooth", ("bluetooth",)),
    ("5g", ("5g",)),
    ("4g", ("4g", "lte")),
    ("anc", (" anc", "noise cancellation")),
    ("enc", (" enc", "environment noise cancellation")),
    ("fast_charging", ("fast charging", "quick charge", "supervooc")),
    ("usb_c", ("type-c", "usb-c", "usb c")),
    ("water_resistant", ("water resistant", "waterproof", "ip55", "ip67", "ip68")),
    ("rechargeable", ("rechargeable",)),
    ("gaming", ("gaming", "low latency")),
    ("amoled", ("amoled",)),
    ("touch_control", ("touch control",)),
)


def derive_features(text: str) -> list[str]:
    found: list[str] = []

    for feature, phrases in FEATURE_RULES:
        if any(phrase in text for phrase in phrases):
            found.append(feature)

    return found


def classify_product(
    product: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    title = str(product.get("title") or "").strip()
    brand = str(product.get("brand") or "").strip()
    current_category = str(product.get("category") or "").strip()
    searchable = normalize(
        " ".join(
            (
                title,
                brand,
                current_category,
                str(product.get("description") or ""),
            )
        )
    )

    product_id = get_product_id(product, position)

    title_text = normalize(title)
    category_text = normalize(current_category)

    is_promotional_listing = (
        any(phrase in title_text for phrase in PROMOTIONAL_PHRASES)
        or category_text in {
            "offers",
            "prime deal electronics",
            "prime deal toys and stationery",
        }
    )

    if is_promotional_listing:
        return {
            "product_id": product_id,
            "title": title,
            "brand": brand,
            "current_category": current_category,
            "classification_status": "excluded_non_product",
            "product_type": "promotional_listing",
            "shopping_category": "Promotions",
            "parent_category": "Promotions",
            "tags": ["promotion"],
            "features": [],
            "buyer_intents": ["deal discovery"],
            "matched_rule": "promotional_listing",
            "matched_phrases": [],
            "confidence": 100,
            "review_required": False,
            "reason": "Listing appears to represent a store promotion, not a product",
        }

    matched: list[tuple[dict[str, Any], list[str]]] = []

    for rule in RULES:
        phrases = tuple(rule["phrases"])
        hits = phrase_match(searchable, phrases)

        if hits:
            matched.append((rule, hits))

    if not matched:
        return {
            "product_id": product_id,
            "title": title,
            "brand": brand,
            "current_category": current_category,
            "classification_status": "manual_review",
            "product_type": "unclassified",
            "shopping_category": current_category or "Unclassified",
            "parent_category": current_category or "Unclassified",
            "tags": [],
            "features": derive_features(searchable),
            "buyer_intents": [],
            "matched_rule": None,
            "matched_phrases": [],
            "confidence": 0,
            "review_required": True,
            "reason": "No deterministic taxonomy rule matched",
        }

    # More matched phrases means stronger evidence. Rule order breaks ties.
    matched.sort(
        key=lambda item: len(item[1]),
        reverse=True,
    )
    best_rule, best_hits = matched[0]

    competing_types = {
        rule["product_type"]
        for rule, _ in matched
    }

    confidence = min(98, 75 + len(best_hits) * 7)

    if len(competing_types) > 1:
        confidence = min(confidence, 82)

    tags = list(dict.fromkeys(best_rule.get("tags", ())))
    features = derive_features(searchable)

    return {
        "product_id": product_id,
        "title": title,
        "brand": brand,
        "current_category": current_category,
        "classification_status": "classified",
        "product_type": best_rule["product_type"],
        "shopping_category": best_rule["shopping_category"],
        "parent_category": best_rule["parent_category"],
        "tags": tags,
        "features": features,
        "buyer_intents": list(best_rule.get("buyer_intents", ())),
        "matched_rule": best_rule["product_type"],
        "matched_phrases": best_hits,
        "candidate_types": sorted(competing_types),
        "confidence": confidence,
        "review_required": confidence < 80 or len(competing_types) > 1,
        "reason": (
            "Matched deterministic product-title taxonomy rule"
            if len(competing_types) == 1
            else "Multiple taxonomy rules matched; strongest rule selected"
        ),
    }


def build_taxonomy() -> dict[str, Any]:
    products = load_json(PRODUCT_DB, [])

    if not isinstance(products, list):
        raise ValueError("coupons.json must contain a JSON list")

    classifications = [
        classify_product(product, position)
        for position, product in enumerate(products, start=1)
        if isinstance(product, dict)
    ]

    product_types = Counter(
        item["product_type"]
        for item in classifications
    )
    shopping_categories = Counter(
        item["shopping_category"]
        for item in classifications
    )

    summary = {
        "total_products": len(classifications),
        "classified": sum(
            1
            for item in classifications
            if item["classification_status"] == "classified"
        ),
        "manual_review": sum(
            1
            for item in classifications
            if item["classification_status"] == "manual_review"
        ),
        "excluded_non_product": sum(
            1
            for item in classifications
            if item["classification_status"] == "excluded_non_product"
        ),
        "review_required": sum(
            1
            for item in classifications
            if item["review_required"] is True
        ),
        "unique_product_types": len(product_types),
        "unique_shopping_categories": len(shopping_categories),
    }

    return {
        "schema_version": "1.1",
        "generated_at": utc_now(),
        "source_file": "coupons.json",
        "summary": summary,
        "product_type_counts": dict(product_types.most_common()),
        "shopping_category_counts": dict(
            shopping_categories.most_common()
        ),
        "products": classifications,
    }


def print_report(payload: dict[str, Any]) -> None:
    summary = payload["summary"]

    print("\n" + "=" * 78)
    print("COUPON WORLD PRODUCT CLASSIFIER")
    print("=" * 78)
    print("Products             :", summary["total_products"])
    print("Classified           :", summary["classified"])
    print("Manual review        :", summary["manual_review"])
    print("Excluded non-product :", summary["excluded_non_product"])
    print("Review required      :", summary["review_required"])
    print("Product types        :", summary["unique_product_types"])
    print("Shopping categories  :", summary["unique_shopping_categories"])
    print("Output               :", OUTPUT_DB)
    print("=" * 78)

    print("\nCLASSIFICATION PREVIEW")
    print("-" * 78)

    for item in payload["products"]:
        print(
            f'{item["product_id"]:>3} | '
            f'{item["product_type"]:<24} | '
            f'{item["confidence"]:>3} | '
            f'{item["title"][:58]}'
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create reviewable product taxonomy for Coupon World"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("build", "status"),
        default="build",
    )
    args = parser.parse_args()

    if args.command == "status":
        payload = load_json(OUTPUT_DB, {"summary": {}, "products": []})

        if not payload.get("products"):
            print("No product taxonomy has been generated yet.")
            return 1

        print_report(payload)
        return 0

    try:
        payload = build_taxonomy()
        save_json(OUTPUT_DB, payload)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
