#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Brain v1.1

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
from pathlib import Path
from typing import Any

from intent_engine import parse_query
from knowledge_engine import load_product_knowledge
from price_engine import analyze_price
from product_scoring import score_product
from recommendation_engine import explain_product


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"

INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
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
    """Filter, score and rank products against parsed intent."""

    matches: list[dict] = []

    category = intent.get("category")

    brands = [
        str(brand).lower()
        for brand in intent.get("brands", [])
        if brand
    ]

    budget_max = intent.get("budget_max")

    for product in products:
        if product.get("active") is False:
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

        if category:
            category_text = str(category).lower()

            if (
                category_text not in product_category
                and category_text not in product_title
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

        ranked_product["score"] = score_product(
            ranked_product,
            intent,
        )

        ranked_product["reasons"] = explain_product(
            ranked_product,
            intent,
        )

        ranked_product["price_info"] = analyze_price(
            ranked_product,
            intent,
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
                "reasons": product.get("reasons", []),
                "link": product.get("link"),
                "category": product.get("category"),
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
    print("COUPON WORLD SHOPPING BRAIN v1.1")
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

        print("Score      :", product.get("score", 0))

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

        products = merge_intelligence(
            products,
            identity_payload,
            feature_payload,
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
