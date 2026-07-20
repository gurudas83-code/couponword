#!/usr/bin/env python3
"""
Coupon World AI Shopping Intelligence Platform
Product Feature Engine v1.0

Purpose:
- Read coupons.json
- Read data/intelligence/product_identity.json
- Extract only explicitly available product features
- Never invent or externally fetch specifications
- Preserve evidence, source and confidence
- Write data/intelligence/product_features.json only with --write

Usage:
    python python/product_feature_engine.py
    python python/product_feature_engine.py --write
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
PRODUCTS_FILE = ROOT / "coupons.json"
IDENTITY_FILE = ROOT / "data" / "intelligence" / "product_identity.json"
OUTPUT_FILE = ROOT / "data" / "intelligence" / "product_features.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def normalized_text(value: Any) -> str:
    return clean_text(value).lower()


def feature_record(
    value: Any,
    raw_value: str,
    source: str,
    confidence: str = "high",
) -> dict[str, Any]:
    return {
        "value": value,
        "raw_value": clean_text(raw_value),
        "source": source,
        "confidence": confidence,
        "verified": False,
    }


def first_match(
    patterns: list[str],
    text: str,
    flags: int = re.IGNORECASE,
) -> re.Match[str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match
    return None


def unique_list(values: list[Any]) -> list[Any]:
    output = []

    for value in values:
        if value not in output:
            output.append(value)

    return output


def normalize_number(value: str) -> int | float:
    number = float(value.replace(",", ""))

    if number.is_integer():
        return int(number)

    return number


def source_texts(product: dict[str, Any]) -> list[tuple[str, str]]:
    """
    Source order matters.

    Product title is preferred because current descriptions are often
    template-generated and repeat the title.
    """
    sources = []

    title = clean_text(product.get("title"))
    description = clean_text(product.get("description"))

    if title:
        sources.append(("product_title", title))

    if description and description.lower() != title.lower():
        sources.append(("product_description", description))

    return sources


# ---------------------------------------------------------------------------
# Feature extractors
# ---------------------------------------------------------------------------

def extract_ram(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{1,3})\s*GB\s*(?:RAM|LPDDR\d?[X]?)\b",
            r"\bRAM\s*[:\-]?\s*(\d{1,3})\s*GB\b",
            r"\b(\d{1,3})\s*GB\s*\+\s*(\d{1,4})\s*GB\b",
        ],
        text,
    )

    if not match:
        return None

    ram_gb = int(match.group(1))

    if ram_gb > 128:
        return None

    return feature_record(
        value={"amount": ram_gb, "unit": "GB"},
        raw_value=match.group(0),
        source=source,
    )


def extract_storage(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{2,4})\s*(GB|TB)\s*(?:Storage|ROM|SSD|HDD)\b",
            r"\b(?:Storage|ROM|SSD|HDD)\s*[:\-]?\s*(\d{2,4})\s*(GB|TB)\b",
            r"\b(\d{1,2})\s*TB\s*(?:SSD|HDD)?\b",
        ],
        text,
    )

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).upper()

    if unit == "GB" and amount < 16:
        return None

    storage_type = None
    raw_lower = match.group(0).lower()

    if "ssd" in raw_lower:
        storage_type = "SSD"
    elif "hdd" in raw_lower:
        storage_type = "HDD"
    elif "rom" in raw_lower:
        storage_type = "ROM"

    return feature_record(
        value={
            "amount": amount,
            "unit": unit,
            "type": storage_type,
        },
        raw_value=match.group(0),
        source=source,
    )


def extract_battery(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{3,6})\s*mAh\b",
            r"\b(\d{1,3}(?:\.\d+)?)\s*Wh\b",
        ],
        text,
    )

    if not match:
        return None

    raw = match.group(0)

    if "mah" in raw.lower():
        value = {
            "amount": normalize_number(match.group(1)),
            "unit": "mAh",
        }
    else:
        value = {
            "amount": normalize_number(match.group(1)),
            "unit": "Wh",
        }

    return feature_record(value, raw, source)


def extract_charging(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{1,3})\s*W\s*(?:Fast|Super|Rapid|Flash|Turbo)?\s*Charging\b",
            r"\b(?:Fast|Super|Rapid|Flash|Turbo)\s*Charging\s*(?:up to)?\s*(\d{1,3})\s*W\b",
            r"\b(\d{1,3})\s*W\s*(?:charger|adapter)\b",
        ],
        text,
    )

    if not match:
        return None

    watts = int(match.group(1))

    if watts > 500:
        return None

    return feature_record(
        value={"amount": watts, "unit": "W"},
        raw_value=match.group(0),
        source=source,
    )


def extract_display_size(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:inch|inches|in|”|\")\s*(?:display|screen|monitor|tablet|laptop|tv)?\b",
            r"\b(\d{1,2}(?:\.\d{1,2})?)\s*-\s*inch\b",
        ],
        text,
    )

    if not match:
        return None

    size = float(match.group(1))

    if size < 1 or size > 100:
        return None

    return feature_record(
        value={"amount": size, "unit": "inch"},
        raw_value=match.group(0),
        source=source,
    )


def extract_resolution(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(4K|8K|Full\s*HD|FHD\+?|HD\+?|QHD\+?|2K)\b",
            r"\b(\d{3,4})\s*[x×]\s*(\d{3,4})\b",
        ],
        text,
    )

    if not match:
        return None

    return feature_record(
        value=clean_text(match.group(0)).upper(),
        raw_value=match.group(0),
        source=source,
    )


def extract_refresh_rate(text: str, source: str) -> dict[str, Any] | None:
    match = re.search(r"\b(\d{2,3})\s*Hz\b", text, re.IGNORECASE)

    if not match:
        return None

    rate = int(match.group(1))

    if rate < 30 or rate > 1000:
        return None

    return feature_record(
        value={"amount": rate, "unit": "Hz"},
        raw_value=match.group(0),
        source=source,
    )


def extract_camera(text: str, source: str) -> dict[str, Any] | None:
    matches = re.findall(
        r"\b(\d{1,3}(?:\.\d+)?)\s*MP\b",
        text,
        re.IGNORECASE,
    )

    if not matches:
        return None

    megapixels = []

    for value in matches:
        mp = normalize_number(value)

        if 0 < mp <= 250 and mp not in megapixels:
            megapixels.append(mp)

    if not megapixels:
        return None

    return feature_record(
        value={
            "megapixels": megapixels,
            "highest_mp": max(megapixels),
        },
        raw_value=", ".join(f"{value}MP" for value in matches),
        source=source,
    )


def extract_processor(text: str, source: str) -> dict[str, Any] | None:
    patterns = [
        r"\b(?:Qualcomm\s+)?Snapdragon\s+[A-Za-z0-9+\- ]{2,30}",
        r"\b(?:MediaTek\s+)?Dimensity\s+[A-Za-z0-9+\- ]{2,25}",
        r"\b(?:MediaTek\s+)?Helio\s+[A-Za-z0-9+\- ]{2,20}",
        r"\bIntel\s+Core\s+(?:Ultra\s+)?[i3579]\s*[- ]?[A-Za-z0-9]+\b",
        r"\bAMD\s+Ryzen\s+[3579]\s+[A-Za-z0-9]+\b",
        r"\bApple\s+[AM]\d+(?:\s+(?:Pro|Max|Ultra))?\b",
        r"\bExynos\s+\d{3,5}\b",
        r"\bTensor\s+G\d\b",
    ]

    match = first_match(patterns, text)

    if not match:
        return None

    value = clean_text(match.group(0)).rstrip(" ,-")

    return feature_record(
        value=value,
        raw_value=match.group(0),
        source=source,
    )


def extract_network(text: str, source: str) -> dict[str, Any] | None:
    networks = []

    for network in ("5G", "4G", "LTE", "Wi-Fi 6E", "Wi-Fi 6", "Wi-Fi", "Bluetooth"):
        if re.search(rf"\b{re.escape(network)}\b", text, re.IGNORECASE):
            networks.append(network)

    networks = unique_list(networks)

    if not networks:
        return None

    return feature_record(
        value=networks,
        raw_value=", ".join(networks),
        source=source,
    )


def extract_audio_features(text: str, source: str) -> dict[str, Any] | None:
    found = []

    feature_patterns = {
        "ANC": r"\b(?:ANC|Active Noise Cancellation)\b",
        "ENC": r"\b(?:ENC|Environmental Noise Cancellation)\b",
        "TWS": r"\bTWS\b",
        "Wired": r"\bWired\b",
        "Dolby Atmos": r"\bDolby Atmos\b",
        "Spatial Audio": r"\bSpatial Audio\b",
    }

    for label, pattern in feature_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(label)

    if not found:
        return None

    return feature_record(
        value=found,
        raw_value=", ".join(found),
        source=source,
    )


def extract_playback_time(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(?:up to\s*)?(\d{1,3})\s*(?:hours|hrs|hour|hr)\s*(?:playback|battery|playtime)\b",
            r"\b(?:playback|playtime)\s*(?:of|up to)?\s*(\d{1,3})\s*(?:hours|hrs|hour|hr)\b",
        ],
        text,
    )

    if not match:
        return None

    hours = int(match.group(1))

    if hours > 500:
        return None

    return feature_record(
        value={"amount": hours, "unit": "hours"},
        raw_value=match.group(0),
        source=source,
    )


def extract_capacity(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d+(?:\.\d+)?)\s*(L|Litres?|Liters?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(ml|millilitres?|milliliters?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(kg|g)\s*(?:capacity)?\b",
        ],
        text,
    )

    if not match:
        return None

    amount = normalize_number(match.group(1))
    unit_raw = match.group(2).lower()

    unit_map = {
        "l": "L",
        "litre": "L",
        "litres": "L",
        "liter": "L",
        "liters": "L",
        "ml": "ml",
        "millilitre": "ml",
        "millilitres": "ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "kg": "kg",
        "g": "g",
    }

    unit = unit_map.get(unit_raw, unit_raw)

    return feature_record(
        value={"amount": amount, "unit": unit},
        raw_value=match.group(0),
        source=source,
    )


def extract_power(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\b(\d{2,5})\s*(W|Watt|Watts)\b",
            r"\b(\d+(?:\.\d+)?)\s*(HP)\b",
        ],
        text,
    )

    if not match:
        return None

    amount = normalize_number(match.group(1))
    unit = match.group(2).upper()

    if unit in {"WATT", "WATTS"}:
        unit = "W"

    return feature_record(
        value={"amount": amount, "unit": unit},
        raw_value=match.group(0),
        source=source,
    )


def extract_material(text: str, source: str) -> dict[str, Any] | None:
    materials = [
        ("Stainless Steel", r"\bstainless steel\b"),
        ("Aluminium", r"\balumini?um\b"),
        ("Silicone", r"\bsilicone\b"),
        ("Leather", r"\bleather\b"),
        ("Cotton", r"\bcotton\b"),
        ("Plastic", r"\bplastic\b"),
        ("Wood", r"\bwood(?:en)?\b"),
        ("Glass", r"\bglass\b"),
        ("Ceramic", r"\bceramic\b"),
        ("Rubber", r"\brubber\b"),
        ("Polyester", r"\bpolyester\b"),
        ("ABS", r"\bABS\b"),
    ]

    found = []

    for label, pattern in materials:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(label)

    if not found:
        return None

    return feature_record(
        value=found,
        raw_value=", ".join(found),
        source=source,
    )


def extract_pack_quantity(text: str, source: str) -> dict[str, Any] | None:
    match = first_match(
        [
            r"\bpack of\s*(\d{1,3})\b",
            r"\bset of\s*(\d{1,3})\b",
            r"\b(\d{1,3})\s*(?:pieces|piece|pcs|pc)\b",
        ],
        text,
    )

    if not match:
        return None

    quantity = int(match.group(1))

    if quantity < 1 or quantity > 1000:
        return None

    return feature_record(
        value={"quantity": quantity, "unit": "pieces"},
        raw_value=match.group(0),
        source=source,
    )


def extract_dimensions(text: str, source: str) -> dict[str, Any] | None:
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)"
        r"(?:\s*[x×]\s*(\d+(?:\.\d+)?))?\s*"
        r"(cm|mm|inch|inches|m)\b",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    values = [
        normalize_number(match.group(1)),
        normalize_number(match.group(2)),
    ]

    if match.group(3):
        values.append(normalize_number(match.group(3)))

    unit = match.group(4).lower()

    if unit == "inches":
        unit = "inch"

    return feature_record(
        value={
            "values": values,
            "unit": unit,
        },
        raw_value=match.group(0),
        source=source,
    )


def extract_color(identity: dict[str, Any]) -> dict[str, Any] | None:
    variant = identity.get("variant")

    if not isinstance(variant, dict):
        return None

    color = clean_text(variant.get("color"))

    if not color:
        return None

    return feature_record(
        value=color,
        raw_value=color,
        source="product_identity",
        confidence="medium",
    )


def extract_model_codes(text: str, source: str) -> dict[str, Any] | None:
    matches = re.findall(
        r"\b(?:SM-[A-Z0-9]{3,10}|[A-Z]{1,4}-\d{2,6}[A-Z0-9-]*)\b",
        text,
        re.IGNORECASE,
    )

    matches = unique_list([clean_text(value).upper() for value in matches])

    if not matches:
        return None

    return feature_record(
        value=matches,
        raw_value=", ".join(matches),
        source=source,
        confidence="medium",
    )


# ---------------------------------------------------------------------------
# Product-level processing
# ---------------------------------------------------------------------------

EXTRACTORS = [
    ("ram", extract_ram),
    ("storage", extract_storage),
    ("battery", extract_battery),
    ("charging", extract_charging),
    ("display_size", extract_display_size),
    ("display_resolution", extract_resolution),
    ("refresh_rate", extract_refresh_rate),
    ("camera", extract_camera),
    ("processor", extract_processor),
    ("connectivity", extract_network),
    ("audio_features", extract_audio_features),
    ("playback_time", extract_playback_time),
    ("capacity", extract_capacity),
    ("power", extract_power),
    ("material", extract_material),
    ("pack_quantity", extract_pack_quantity),
    ("dimensions", extract_dimensions),
    ("model_codes", extract_model_codes),
]


def extract_product_features(
    product: dict[str, Any],
    identity: dict[str, Any],
    source_index: int,
) -> dict[str, Any]:
    product_id = str(
        product.get("id")
        or product.get("sl_no")
        or identity.get("product_id")
        or source_index
    )

    features: dict[str, Any] = {}
    evidence = []
    warnings = []

    for source_name, text in source_texts(product):
        for feature_name, extractor in EXTRACTORS:
            if feature_name in features:
                continue

            result = extractor(text, source_name)

            if result is not None:
                features[feature_name] = result
                evidence.append(
                    f"{feature_name} extracted from {source_name}"
                )

    color = extract_color(identity)

    if color is not None:
        features["color"] = color
        evidence.append("color inherited from product identity")

    identity_variant = identity.get("variant", {})

    if isinstance(identity_variant, dict):
        if "ram" not in features and identity_variant.get("ram"):
            features["ram"] = feature_record(
                value=identity_variant["ram"],
                raw_value=str(identity_variant["ram"]),
                source="product_identity",
                confidence="medium",
            )
            evidence.append("ram inherited from product identity")

        if "storage" not in features and identity_variant.get("storage"):
            features["storage"] = feature_record(
                value=identity_variant["storage"],
                raw_value=str(identity_variant["storage"]),
                source="product_identity",
                confidence="medium",
            )
            evidence.append("storage inherited from product identity")

    feature_count = len(features)

    if feature_count == 0:
        confidence_score = 0
        confidence_level = "low"
        warnings.append("no explicit technical feature found")
    else:
        high_count = sum(
            1
            for feature in features.values()
            if feature.get("confidence") == "high"
        )
        medium_count = sum(
            1
            for feature in features.values()
            if feature.get("confidence") == "medium"
        )

        confidence_score = min(
            100,
            (high_count * 18) + (medium_count * 10) + 25,
        )

        if confidence_score >= 75:
            confidence_level = "high"
        elif confidence_score >= 40:
            confidence_level = "medium"
        else:
            confidence_level = "low"

    if not product.get("description"):
        warnings.append("product description unavailable")

    warnings.append(
        "features are extracted from existing product data and are not manufacturer-verified"
    )

    return {
        "product_id": product_id,
        "source_index": source_index,
        "title": clean_text(product.get("title")),
        "brand": identity.get("brand") or product.get("brand"),
        "category": identity.get("category") or product.get("category"),
        "subcategory": identity.get("subcategory"),
        "asin": identity.get("asin") or product.get("asin"),
        "features": features,
        "feature_count": feature_count,
        "feature_confidence": {
            "score": confidence_score,
            "level": confidence_level,
        },
        "evidence": evidence,
        "warnings": unique_list(warnings),
    }


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: File not found: {path.relative_to(ROOT)}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON in {path.relative_to(ROOT)}")
        print(f"Line {exc.lineno}, column {exc.colno}: {exc.msg}")
        sys.exit(1)


def load_products() -> list[dict[str, Any]]:
    data = load_json(PRODUCTS_FILE)

    if not isinstance(data, list):
        print("ERROR: coupons.json must contain a JSON list.")
        sys.exit(1)

    return [item for item in data if isinstance(item, dict)]


def load_identities() -> list[dict[str, Any]]:
    data = load_json(IDENTITY_FILE)

    if not isinstance(data, dict):
        print("ERROR: product_identity.json must contain a JSON object.")
        sys.exit(1)

    products = data.get("products")

    if not isinstance(products, list):
        print(
            "ERROR: product_identity.json must contain a 'products' list."
        )
        sys.exit(1)

    return [item for item in products if isinstance(item, dict)]


def identity_lookup(
    identities: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    lookup = {}

    for identity in identities:
        product_id = identity.get("product_id")

        if product_id is not None:
            lookup[str(product_id)] = identity

    return lookup


# ---------------------------------------------------------------------------
# Reporting and writing
# ---------------------------------------------------------------------------

def build_output(
    products: list[dict[str, Any]],
    identities: list[dict[str, Any]],
) -> dict[str, Any]:
    identities_by_id = identity_lookup(identities)
    output_products = []

    for index, product in enumerate(products, start=1):
        product_id = str(
            product.get("id")
            or product.get("sl_no")
            or index
        )

        identity = identities_by_id.get(product_id, {})

        output_products.append(
            extract_product_features(
                product=product,
                identity=identity,
                source_index=index,
            )
        )

    total_features = sum(
        product["feature_count"]
        for product in output_products
    )

    products_with_features = sum(
        1
        for product in output_products
        if product["feature_count"] > 0
    )

    products_without_features = (
        len(output_products) - products_with_features
    )

    confidence_counter = Counter(
        product["feature_confidence"]["level"]
        for product in output_products
    )

    feature_counter = Counter()

    for product in output_products:
        feature_counter.update(product["features"].keys())

    return {
        "engine": {
            "name": "Coupon World Product Feature Engine",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "explicit-extraction-only",
            "external_lookup": False,
            "manufacturer_verified": False,
            "source_files": [
                "coupons.json",
                "data/intelligence/product_identity.json",
            ],
        },
        "summary": {
            "total_products": len(output_products),
            "products_with_features": products_with_features,
            "products_without_features": products_without_features,
            "total_features_extracted": total_features,
            "average_features_per_product": round(
                total_features / len(output_products), 2
            ) if output_products else 0,
            "confidence": {
                "high": confidence_counter.get("high", 0),
                "medium": confidence_counter.get("medium", 0),
                "low": confidence_counter.get("low", 0),
            },
            "feature_coverage": dict(
                feature_counter.most_common()
            ),
        },
        "products": output_products,
    }


def print_report(output: dict[str, Any], write_mode: bool) -> None:
    summary = output["summary"]

    print("=" * 66)
    print("COUPON WORLD PRODUCT FEATURE ENGINE v1.0")
    print("=" * 66)
    print(f"Products processed        : {summary['total_products']}")
    print(f"Products with features    : {summary['products_with_features']}")
    print(f"Products without features : {summary['products_without_features']}")
    print(f"Total features extracted  : {summary['total_features_extracted']}")
    print(
        "Average features/product : "
        f"{summary['average_features_per_product']}"
    )

    print("\nConfidence")
    print("-" * 66)
    print(f"High   : {summary['confidence']['high']}")
    print(f"Medium : {summary['confidence']['medium']}")
    print(f"Low    : {summary['confidence']['low']}")

    print("\nTop extracted feature types")
    print("-" * 66)

    coverage = summary["feature_coverage"]

    if coverage:
        for feature_name, count in list(coverage.items())[:15]:
            print(f"{feature_name:<22}: {count}")
    else:
        print("No explicit features found.")

    print("\nSample preview")
    print("-" * 66)

    preview_products = [
        product
        for product in output["products"]
        if product["feature_count"] > 0
    ][:3]

    if not preview_products:
        print("No product with extracted features available.")
    else:
        for product in preview_products:
            print(
                f"\nProduct {product['product_id']}: "
                f"{product['title'][:90]}"
            )

            for feature_name, feature in product["features"].items():
                print(
                    f"  - {feature_name}: {feature['value']} "
                    f"[{feature['source']}, "
                    f"{feature['confidence']}]"
                )

    print("\n" + "=" * 66)

    if write_mode:
        print(
            "OUTPUT WRITTEN: "
            "data/intelligence/product_features.json"
        )
    else:
        print("DRY RUN ONLY — no file was changed.")
        print(
            "Run with --write after reviewing the report:"
        )
        print(
            "python python/product_feature_engine.py --write"
        )

    print("=" * 66)


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = path.with_suffix(path.suffix + ".tmp")

    temporary_file.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_file.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract explicit product features from Coupon World data."
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Write data/intelligence/product_features.json",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    products = load_products()
    identities = load_identities()

    if len(products) != len(identities):
        print(
            "WARNING: Product and identity record counts differ: "
            f"{len(products)} products vs {len(identities)} identities."
        )

    output = build_output(products, identities)

    if args.write:
        atomic_write(OUTPUT_FILE, output)

    print_report(output, write_mode=args.write)


if __name__ == "__main__":
    main()
