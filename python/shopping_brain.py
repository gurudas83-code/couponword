#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Brain v1.2

Purpose:
- Accept a shopping query
- Parse shopping intent
- Load products
- Merge product identity and feature intelligence
- Merge verified product knowledge
- Match and score products
- Explain recommendations
- Show price intelligence
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from intent_engine import parse_query
from knowledge_engine import load_product_knowledge
from price_engine import analyze_price
from product_scoring import score_product
from recommendation_engine import build_requirement_assessment, explain_product


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"

INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
TAXONOMY_DB = INTELLIGENCE_DIR / "product_taxonomy.json"
IDENTITY_DB = INTELLIGENCE_DIR / "product_identity.json"
FEATURE_DB = INTELLIGENCE_DIR / "product_features.json"


def _load_database(path: Path) -> dict[str, Any]:
    """Safely load a JSON dictionary."""

    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}

    if isinstance(data, dict):
        return data

    return {}


def load_identity_database() -> dict[str, Any]:
    return _load_database(IDENTITY_DB)


def load_feature_database() -> dict[str, Any]:
    return _load_database(FEATURE_DB)



def load_taxonomy_database() -> dict[str, Any]:
    """Load the generated product taxonomy database."""
    return _load_database(TAXONOMY_DB)


def load_products() -> list[dict]:
    """Load the main Coupon World product database."""

    if not DB.exists():
        raise FileNotFoundError(f"Product database not found: {DB}")

    try:
        data = json.loads(DB.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(
            "coupons.json must use UTF-8 encoding"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"coupons.json contains invalid JSON: {error}"
        ) from error

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")

    return [
        product
        for product in data
        if isinstance(product, dict)
    ]


def _index_by_product_id(
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Create a product intelligence index using product_id."""

    index: dict[str, dict[str, Any]] = {}

    products = payload.get("products", [])

    if not isinstance(products, list):
        return index

    for item in products:
        if not isinstance(item, dict):
            continue

        product_id = item.get("product_id")

        if product_id not in (None, ""):
            index[str(product_id)] = item

    return index


def merge_intelligence(
    products: list[dict],
    identity_payload: dict[str, Any],
    feature_payload: dict[str, Any],
) -> list[dict]:
    """Merge identity and feature intelligence into each product."""

    identity_index = _index_by_product_id(identity_payload)
    feature_index = _index_by_product_id(feature_payload)

    merged_products: list[dict] = []

    for position, product in enumerate(products, start=1):
        merged = product.copy()

        product_id = (
            product.get("id")
            or product.get("sl_no")
            or product.get("asin")
            or position
        )

        product_key = str(product_id)

        merged["identity"] = identity_index.get(product_key, {})
        merged["features"] = feature_index.get(product_key, {})

        merged_products.append(merged)

    return merged_products


def merge_taxonomy(
    products: list[dict],
    taxonomy_payload: dict[str, Any],
) -> list[dict]:
    """Attach product taxonomy to every product using product_id."""
    taxonomy_index = _index_by_product_id(taxonomy_payload)
    merged_products: list[dict] = []

    for position, product in enumerate(products, start=1):
        merged = product.copy()

        product_id = (
            product.get("id")
            or product.get("sl_no")
            or product.get("product_id")
            or product.get("asin")
            or position
        )

        merged["taxonomy"] = taxonomy_index.get(
            str(product_id),
            {},
        )
        merged_products.append(merged)

    return merged_products


QUERY_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "computer_keyboard": (
        "keyboard",
        "wireless keyboard",
        "computer keyboard",
        "office keyboard",
        "keyboard mouse combo",
        "keyboard and mouse",
    ),
    "tablet_keyboard_case": (
        "keyboard case",
        "tablet keyboard",
        "folio keyboard",
    ),
    "computer_mouse": (
        "mouse",
        "wireless mouse",
        "office mouse",
        "gaming mouse",
    ),
    "earbuds": (
        "earbuds",
        "ear buds",
        "tws",
        "airpods",
        "airdopes",
        "buds",
    ),
    "headphones": (
        "headphones",
        "headphone",
        "headset",
    ),
    "smartphone": (
        "phone",
        "smartphone",
        "mobile",
        "iphone",
        "android phone",
        "5g phone",
    ),
    "laptop": (
        "laptop",
        "gaming laptop",
        "notebook",
    ),
    "smartwatch": (
        "smartwatch",
        "smart watch",
        "fitness watch",
    ),
    "bluetooth_speaker": (
        "bluetooth speaker",
        "wireless speaker",
        "portable speaker",
    ),
    "memory_card": (
        "memory card",
        "micro sd",
        "microsd",
        "sd card",
    ),
    "power_bank": (
        "power bank",
        "powerbank",
    ),
    "telescope": (
        "telescope",
        "astronomy telescope",
    ),
    "running_shoes": (
        "running shoes",
        "shoes",
        "sneakers",
    ),
    "microwave_oven": (
        "microwave",
        "microwave oven",
    ),
    "water_bottle": (
        "water bottle",
        "bottle",
        "flask",
    ),
}


def _normalize_query_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9+\s.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def infer_requested_product_types(intent: dict) -> set[str]:
    """Infer precise product types even when Intent Engine category is None."""
    query_text = _normalize_query_text(
        " ".join(intent.get("keywords", []))
    )
    requested: set[str] = set()

    for product_type, aliases in QUERY_TYPE_ALIASES.items():
        if any(alias in query_text for alias in aliases):
            requested.add(product_type)

    category = _normalize_query_text(intent.get("category"))

    if category:
        for product_type, aliases in QUERY_TYPE_ALIASES.items():
            if category == product_type or any(
                category in alias or alias in category
                for alias in aliases
            ):
                requested.add(product_type)

    return requested


def taxonomy_search_text(product: dict) -> str:
    taxonomy = product.get("taxonomy", {})

    if not isinstance(taxonomy, dict):
        taxonomy = {}

    values: list[str] = [
        product.get("title", ""),
        product.get("brand", ""),
        product.get("category", ""),
        taxonomy.get("product_type", ""),
        taxonomy.get("shopping_category", ""),
        taxonomy.get("parent_category", ""),
    ]

    for field in ("tags", "features", "buyer_intents"):
        field_values = taxonomy.get(field, [])

        if isinstance(field_values, list):
            values.extend(str(value) for value in field_values)

    return _normalize_query_text(" ".join(str(value) for value in values))


def taxonomy_match_score(
    product: dict,
    intent: dict,
    requested_types: set[str],
) -> tuple[int, list[str]]:
    taxonomy = product.get("taxonomy", {})

    if not isinstance(taxonomy, dict):
        return 0, []

    score = 0
    reasons: list[str] = []
    product_type = str(taxonomy.get("product_type") or "")
    taxonomy_features = {
        _normalize_query_text(value)
        for value in taxonomy.get("features", [])
        if value
    }
    taxonomy_tags = {
        _normalize_query_text(value)
        for value in taxonomy.get("tags", [])
        if value
    }

    if requested_types and product_type in requested_types:
        score += 70
        reasons.append(
            f"Exact product type matched: {product_type.replace('_', ' ')}"
        )

    requested_features = {
        _normalize_query_text(value)
        for value in intent.get("features", [])
        if value
    }

    query_text = _normalize_query_text(
        " ".join(intent.get("keywords", []))
    )

    for feature in (
        "wireless",
        "bluetooth",
        "gaming",
        "anc",
        "enc",
        "5g",
        "amoled",
        "rechargeable",
        "usb_c",
    ):
        if feature.replace("_", " ") in query_text:
            requested_features.add(feature)

    matched_features = requested_features.intersection(
        taxonomy_features.union(taxonomy_tags)
    )

    if matched_features:
        score += min(20, 10 * len(matched_features))
        reasons.append(
            "Feature matched: "
            + ", ".join(sorted(matched_features))
        )

    brands = {
        _normalize_query_text(value)
        for value in intent.get("brands", [])
        if value
    }
    product_brand = _normalize_query_text(product.get("brand"))

    if brands and any(
        brand in product_brand or product_brand in brand
        for brand in brands
    ):
        score += 10
        reasons.append("Preferred brand matched")

    taxonomy_confidence = int(taxonomy.get("confidence") or 0)

    if taxonomy_confidence >= 80:
        score += 5

    return score, reasons



def knowledge_match_score(
    product: dict,
    intent: dict,
) -> tuple[int, list[str]]:
    """Score verified product knowledge against requested features."""

    knowledge = product.get("product_knowledge", {})

    if not isinstance(knowledge, dict) or not knowledge:
        return 0, []

    values: list[str] = []

    for field in ("features", "best_for"):
        field_values = knowledge.get(field, [])

        if isinstance(field_values, list):
            values.extend(
                str(value)
                for value in field_values
                if value
            )

    knowledge_text = _normalize_query_text(" ".join(values))

    requested_terms = {
        _normalize_query_text(value)
        for value in intent.get("features", [])
        if value
    }

    query_text = _normalize_query_text(
        " ".join(intent.get("keywords", []))
    )

    aliases = {
        "amoled": ("amoled", "oled"),
        "oled": ("amoled", "oled"),
        "ip68": ("ip68",),
        "wireless charging": (
            "wireless charging",
            "reverse wireless charging",
        ),
        "wireless": ("wireless", "wireless charging"),
        "snapdragon": ("snapdragon",),
        "gaming": (
            "gaming",
            "snapdragon",
            "120hz",
            "high refresh",
            "lpddr",
            "ufs",
        ),
        "battery": ("battery", "mah"),
        "fast charging": (
            "fast charging",
            "wired charging",
        ),
        "bluetooth": ("bluetooth",),
        "wifi": ("wi fi", "wifi"),
        "office": ("office", "typing", "work"),
    }

    for requested in aliases:
        if requested in query_text:
            requested_terms.add(requested)

    score = 0
    reasons: list[str] = []

    for requested in sorted(requested_terms):
        variants = aliases.get(requested, (requested,))

        if not any(
            variant in knowledge_text
            for variant in variants
        ):
            continue

        if requested in {"amoled", "oled", "ip68"}:
            bonus = 25
        elif requested in {
            "wireless charging",
            "snapdragon",
            "gaming",
        }:
            bonus = 20
        else:
            bonus = 15

        score += bonus
        reasons.append(
            f"Verified knowledge matched: {requested}"
        )

    confidence = knowledge.get("confidence", {})

    if isinstance(confidence, dict):
        confidence_level = str(
            confidence.get("level") or ""
        ).lower()

        if confidence_level == "high" and reasons:
            score += 10
            reasons.append(
                "High-confidence official product knowledge"
            )

    return score, reasons




def knowledge_gate_adjustment(
    product: dict,
    intent: dict,
    knowledge_reasons: list[str],
) -> tuple[int, list[str]]:
    """
    Penalize products whose published verified knowledge does not support
    the user's explicitly requested features.

    Products without published knowledge are not rejected here because their
    feature status is unknown rather than disproved.
    """

    requested = [
        _normalize_query_text(value)
        for value in intent.get("features", [])
        if value
    ]

    if not requested:
        return 0, []

    knowledge = product.get("product_knowledge", {})

    if not isinstance(knowledge, dict) or not knowledge:
        return 0, []

    matched = {
        reason.split(":", 1)[1].strip()
        for reason in knowledge_reasons
        if isinstance(reason, str)
        and reason.lower().startswith("verified knowledge matched:")
        and ":" in reason
    }

    requested_set = set(requested)
    matched_count = len(requested_set & matched)

    if matched_count == len(requested_set):
        return 0, []

    missing_count = len(requested_set) - matched_count

    if matched_count == 0:
        penalty = -40
        message = (
            "Verified knowledge does not support the requested feature"
        )
    else:
        penalty = -15 * missing_count
        message = (
            f"Verified knowledge is missing {missing_count} "
            "requested feature(s)"
        )

    return penalty, [message]


def build_decision_summary(product: dict) -> dict[str, list[str]]:
    """Build a concise user-facing recommendation explanation."""

    knowledge = product.get("product_knowledge", {})
    assessment = product.get("requirement_assessment", {})
    reasons = product.get("reasons", [])

    if not isinstance(knowledge, dict):
        knowledge = {}

    if not isinstance(assessment, dict):
        assessment = {}

    if not isinstance(reasons, list):
        reasons = []

    features = knowledge.get("features", [])
    best_for = knowledge.get("best_for", [])
    limitations = knowledge.get("limitations", [])
    confidence = knowledge.get("confidence", {})

    if not isinstance(features, list):
        features = []

    if not isinstance(best_for, list):
        best_for = []

    if not isinstance(limitations, list):
        limitations = []

    recommended_because: list[str] = []

    for reason in reasons:
        text = str(reason or "").strip()

        if not text:
            continue

        lowered = text.lower()

        if lowered.startswith("verified knowledge matched:"):
            matched = text.split(":", 1)[1].strip()
            recommended_because.append(
                f"Verified requirement matched: {matched}"
            )
        elif lowered == "high-confidence official product knowledge":
            recommended_because.append(
                "High-confidence official product knowledge"
            )

    for feature in features:
        text = str(feature or "").strip()

        if text and text not in recommended_because:
            recommended_because.append(text)

        if len(recommended_because) >= 6:
            break

    if isinstance(confidence, dict):
        confidence_level = str(
            confidence.get("level") or ""
        ).strip().lower()

        if confidence_level == "high":
            verified_text = (
                "Official specifications verified with high confidence"
            )

            if verified_text not in recommended_because:
                recommended_because.append(verified_text)

    requirement_match = int(
        assessment.get("requirement_match_percent") or 0
    )

    if requirement_match >= 100:
        match_text = "All stated requirements matched"

        if match_text not in recommended_because:
            recommended_because.insert(0, match_text)

    return {
        "recommended_because": recommended_because[:7],
        "best_suited_for": [
            str(item).strip()
            for item in best_for[:5]
            if str(item or "").strip()
        ],
        "keep_in_mind": [
            str(item).strip()
            for item in limitations[:4]
            if str(item or "").strip()
        ],
    }


def merge_product_knowledge(
    products: list[dict],
    knowledge_db: dict[str, dict],
) -> list[dict]:
    """
    Merge verified Product Knowledge profiles into product records.

    The current Knowledge Engine indexes profiles by product title.
    Title matching is case-insensitive.
    """

    merged_products: list[dict] = []

    normalized_knowledge = {
        str(title).strip().lower(): profile
        for title, profile in knowledge_db.items()
        if isinstance(profile, dict)
    }

    for product in products:
        merged = product.copy()

        title_key = str(
            product.get("title", "")
        ).strip().lower()

        knowledge = normalized_knowledge.get(title_key, {})

        merged["product_knowledge"] = knowledge

        # Use verified knowledge only when the main product record
        # does not already provide the value.
        if not merged.get("brand") and knowledge.get("brand"):
            merged["brand"] = knowledge["brand"]

        merged_products.append(merged)

    return merged_products


def match_products(
    products: list[dict],
    intent: dict,
) -> list[dict]:
    """Filter, score and rank products using taxonomy and parsed intent."""
    matches: list[dict] = []
    category = intent.get("category")
    requested_types = infer_requested_product_types(intent)

    brands = [
        str(brand).lower()
        for brand in intent.get("brands", [])
        if brand
    ]
    budget_max = intent.get("budget_max")

    for product in products:
        if product.get("active") is False:
            continue

        taxonomy = product.get("taxonomy", {})

        if not isinstance(taxonomy, dict):
            taxonomy = {}

        if taxonomy.get("classification_status") == "excluded_non_product":
            continue

        product_category = str(
            product.get("category", "")
        ).lower()
        product_brand = str(
            product.get("brand", "")
        ).lower()
        product_title = str(
            product.get("title", "")
        ).lower()
        product_type = str(
            taxonomy.get("product_type", "")
        )
        searchable = taxonomy_search_text(product)

        if requested_types:
            if product_type not in requested_types:
                continue
        elif category:
            category_text = str(category).lower()

            if (
                category_text not in product_category
                and category_text not in product_title
                and category_text not in searchable
            ):
                continue

        if brands:
            brand_matched = any(
                brand in product_brand
                or brand in product_title
                for brand in brands
            )

            if not brand_matched:
                continue

        if budget_max is not None:
            price = product.get("price")

            if price not in (None, ""):
                try:
                    numeric_price = float(price)

                    if numeric_price > float(budget_max):
                        continue
                except (TypeError, ValueError):
                    pass

        ranked_product = product.copy()

        base_score = score_product(
            ranked_product,
            intent,
        )
        taxonomy_score, taxonomy_reasons = taxonomy_match_score(
            ranked_product,
            intent,
            requested_types,
        )
        knowledge_score, knowledge_reasons = knowledge_match_score(
            ranked_product,
            intent,
        )
        gate_score, gate_reasons = knowledge_gate_adjustment(
            ranked_product,
            intent,
            knowledge_reasons,
        )

        ranked_product["score"] = (
            base_score
            + taxonomy_score
            + knowledge_score
            + gate_score
        )

        existing_reasons = explain_product(
            ranked_product,
            intent,
        )

        if not isinstance(existing_reasons, list):
            existing_reasons = []

        ranked_product["reasons"] = (
            taxonomy_reasons
            + knowledge_reasons
            + gate_reasons
            + existing_reasons
        )

        ranked_product["price_info"] = analyze_price(
            ranked_product,
            intent,
        )

        ranked_product["requirement_assessment"] = (
            build_requirement_assessment(ranked_product)
        )
        ranked_product["decision_summary"] = build_decision_summary(
            ranked_product
        )

        matches.append(ranked_product)

    matches.sort(
        key=lambda product: product.get("score", 0),
        reverse=True,
    )

    return matches


def build_response(
    query: str,
    intent: dict,
    matches: list[dict],
) -> dict:
    """Return Shopping Brain results as JSON-compatible data."""

    response = {
        "query": query,
        "intent": intent,
        "total_matches": len(matches),
        "matches": [],
    }

    for product in matches[:10]:
        price_info = product.get("price_info", {})
        knowledge = product.get("product_knowledge", {})

        assessment = product.get(
            "requirement_assessment",
            {},
        )

        response["matches"].append(
            {
                "id": product.get("id"),
                "title": product.get("title"),
                "brand": product.get("brand"),
                "price": price_info.get("price"),
                "mrp": price_info.get("mrp"),
                "discount": price_info.get(
                    "discount_percent"
                ),
                "score": product.get("score"),
                "requirement_match_percent": assessment.get(
                    "requirement_match_percent",
                    0,
                ),
                "data_confidence_percent": assessment.get(
                    "data_confidence_percent",
                    0,
                ),
                "recommendation_confidence": assessment.get(
                    "recommendation_confidence",
                    "low",
                ),
                "ai_top_suggestion": len(response["matches"]) == 0,
                "matched_requirements": assessment.get(
                    "matched_requirements",
                    [],
                ),
                "unverified_requirements": assessment.get(
                    "unverified_requirements",
                    [],
                ),
                "reasons": product.get("reasons", []),
                "decision_summary": product.get(
                    "decision_summary",
                    {},
                ),
                "link": product.get("link"),
                "category": product.get("category"),
                "taxonomy": product.get("taxonomy", {}),
                "knowledge": {
                    "features": knowledge.get(
                        "features", []
                    ),
                    "best_for": knowledge.get(
                        "best_for", []
                    ),
                    "limitations": knowledge.get(
                        "limitations", []
                    ),
                    "confidence": knowledge.get(
                        "confidence", {}
                    ),
                },
            }
        )

    return response


def print_text_response(
    intent: dict,
    products: list[dict],
    matches: list[dict],
) -> None:
    """Print Shopping Brain output in a readable terminal format."""

    print("\n" + "=" * 64)
    print("COUPON WORLD SHOPPING BRAIN v1.2")
    print("=" * 64)

    print("Intent          :", intent.get("intent"))
    print("Category        :", intent.get("category"))
    print("Budget minimum  :", intent.get("budget_min"))
    print("Budget maximum  :", intent.get("budget_max"))

    print(
        "Features        :",
        ", ".join(intent.get("features", [])) or "Any",
    )

    print(
        "Brands          :",
        ", ".join(intent.get("brands", [])) or "Any",
    )

    print("-" * 64)

    products_with_knowledge = sum(
        1
        for product in products
        if product.get("product_knowledge")
    )

    print("Products loaded :", len(products))
    print("Knowledge linked:", products_with_knowledge)
    print("Matches found   :", len(matches))

    if not matches:
        print("\nNo matching products found.")
        return

    for position, product in enumerate(
        matches[:10],
        start=1,
    ):
        print("\n" + "=" * 64)
        print(f"RECOMMENDATION #{position}")
        print("=" * 64)

        print(
            "Title      :",
            product.get("title") or "Untitled product",
        )

        print(
            "ID         :",
            product.get("id")
            or product.get("sl_no")
            or "No ID",
        )

        print(
            "Brand      :",
            product.get("brand") or "Unknown",
        )

        price_info = product.get("price_info", {})

        if price_info.get("price_available"):
            price = price_info.get("price")

            if isinstance(price, (int, float)):
                print(f"Price      : {price:.2f}")
            else:
                print("Price      :", price)
        else:
            print("Price      : Price unavailable")

        mrp = price_info.get("mrp")

        if mrp is not None:
            if isinstance(mrp, (int, float)):
                print(f"MRP        : {mrp:.2f}")
            else:
                print("MRP        :", mrp)

        discount = price_info.get("discount_percent")

        if discount is not None:
            print(f"Discount   : {discount}%")

        if price_info.get("within_budget") is True:
            print("Budget     : Within budget")
        elif price_info.get("within_budget") is False:
            print("Budget     : Above budget")

        assessment = product.get(
            "requirement_assessment",
            {},
        )

        if position == 1:
            print("AI Suggestion: Top match for your current requirement")

        print("Score      :", product.get("score", 0))
        print(
            "Requirement match:",
            f"{assessment.get('requirement_match_percent', 0)}%",
        )
        print(
            "Data confidence  :",
            f"{assessment.get('data_confidence_percent', 0)}%",
        )
        print(
            "AI confidence    :",
            str(
                assessment.get(
                    "recommendation_confidence",
                    "low",
                )
            ).title(),
        )

        taxonomy = product.get("taxonomy", {})

        if taxonomy:
            print(
                "Product type:",
                taxonomy.get("product_type", "unclassified"),
            )
            print(
                "Shopping cat:",
                taxonomy.get("shopping_category", "unknown"),
            )

        knowledge = product.get("product_knowledge", {})

        if knowledge:
            confidence = knowledge.get("confidence", {})

            print(
                "Knowledge  :",
                confidence.get("level", "available"),
            )

            features = knowledge.get("features", [])

            if features:
                print("\nVerified product knowledge:")

                for feature in features:
                    print("  -", feature)

            best_for = knowledge.get("best_for", [])

            if best_for:
                print("\nBest for:")

                for use_case in best_for:
                    print("  -", use_case)

            limitations = knowledge.get(
                "limitations",
                [],
            )

            if limitations:
                print("\nLimitations:")

                for limitation in limitations:
                    print("  -", limitation)

        decision = product.get(
            "decision_summary",
            {},
        )

        if isinstance(decision, dict):
            recommended = decision.get(
                "recommended_because",
                [],
            )
            suited = decision.get(
                "best_suited_for",
                [],
            )
            cautions = decision.get(
                "keep_in_mind",
                [],
            )

            if recommended:
                print("\nRecommended because:")

                for item in recommended:
                    print("  ✓", item)

            if suited:
                print("\nBest suited for:")

                for item in suited:
                    print("  ✓", item)

            if cautions:
                print("\nKeep in mind:")

                for item in cautions:
                    print("  •", item)

        print("\nWhy this product?")

        reasons = product.get("reasons", [])

        if reasons:
            for reason in reasons:
                print("  -", reason)
        else:
            print("  - No explanation available")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coupon World Shopping Brain"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text",
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Shopping query",
    )

    args = parser.parse_args()

    if args.query:
        query = " ".join(args.query).strip()
    else:
        query = input("Shopping Query > ").strip()

    if not query:
        print("ERROR: Shopping query is required.")
        return 1

    try:
        intent = parse_query(query)

        products = load_products()

        identity_payload = load_identity_database()
        feature_payload = load_feature_database()
        taxonomy_payload = load_taxonomy_database()

        products = merge_intelligence(
            products,
            identity_payload,
            feature_payload,
        )

        products = merge_taxonomy(
            products,
            taxonomy_payload,
        )

        knowledge_db = load_product_knowledge()

        products = merge_product_knowledge(
            products,
            knowledge_db,
        )

        matches = match_products(
            products,
            intent,
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(f"ERROR: {error}")
        return 1

    if args.json:
        print(
            json.dumps(
                build_response(
                    query,
                    intent,
                    matches,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )

        return 0

    print_text_response(
        intent,
        products,
        matches,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
