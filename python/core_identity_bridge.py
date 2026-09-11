from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from product_evidence_store import build_model_key
from product_identity_v2 import build_identity


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DB = ROOT / "coupons.json"


def clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def load_catalog_products() -> list[dict[str, Any]]:
    if not PRODUCT_DB.exists():
        return []

    data = json.loads(PRODUCT_DB.read_text(encoding="utf-8"))

    if isinstance(data, list):
        products = data
    elif isinstance(data, dict) and isinstance(data.get("products"), list):
        products = data["products"]
    else:
        return []

    return [p for p in products if isinstance(p, dict)]



def _family_tokens(value: Any) -> set[str]:
    """
    Build conservative product-family tokens.

    Retailer colour wording such as Serene or Velvet must not create
    different product families. Generic commerce words are ignored.
    """
    import re

    text = clean(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)

    ignored = {
        "mobile",
        "smartphone",
        "phone",
        "serene",
        "velvet",
        "black",
        "blue",
        "green",
        "white",
        "gold",
        "silver",
        "grey",
        "gray",
    }

    return {
        token
        for token in text.split()
        if token not in ignored
    }


def resolve_family_identity(
    *,
    brand: Any = "",
    model: Any = "",
    title: Any = "",
) -> dict[str, Any] | None:
    """
    Resolve only a unique conservative catalog product-family match.

    This is weaker than exact ASIN/model-key identity and therefore must
    never replace retailer SKU identity. It only supplies the stable
    Coupon World catalog family when the match is unique.

    No fuzzy similarity.
    No ASIN invention.
    No retailer SKU replacement.
    """

    live_brand = clean(brand).casefold()
    live_tokens = _family_tokens(model or title)

    if not live_brand or not live_tokens:
        return None

    products = load_catalog_products()
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for index, product in enumerate(products, start=1):
        identity = build_identity(product, index)

        if clean(identity.get("brand")).casefold() != live_brand:
            continue

        catalog_tokens = _family_tokens(
            identity.get("model")
            or identity.get("search_name")
            or product.get("title")
        )

        if catalog_tokens != live_tokens:
            continue

        matches.append((product, identity))

    if len(matches) != 1:
        return None

    product, identity = matches[0]

    return {
        "match_mode": "product_family",
        "product_id": clean(identity.get("product_id")),
        "asin": clean(identity.get("asin")),
        "brand": clean(identity.get("brand")),
        "model": clean(identity.get("model")),
        "search_name": clean(identity.get("search_name")),
        "title": clean(product.get("title")),
    }


def resolve_stable_identity(
    *,
    asin: Any = "",
    brand: Any = "",
    model: Any = "",
    search_name: Any = "",
    title: Any = "",
) -> dict[str, Any] | None:
    """
    Resolve a live Core identity to an existing Coupon World catalog identity.

    Conservative rules only:
      1. Exact ASIN match.
      2. Unique exact brand+model key match.

    No fuzzy matching.
    No product-family guessing.
    No ASIN invention.
    """
    products = load_catalog_products()
    identities: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for index, product in enumerate(products, start=1):
        identity = build_identity(product, index)
        identities.append((product, identity))

    asin_key = clean(asin).upper()

    if asin_key:
        matches = [
            (product, identity)
            for product, identity in identities
            if clean(identity.get("asin")).upper() == asin_key
        ]

        if len(matches) == 1:
            product, identity = matches[0]
            return {
                "match_mode": "asin",
                "product_id": clean(identity.get("product_id")),
                "asin": clean(identity.get("asin")),
                "brand": clean(identity.get("brand")),
                "model": clean(identity.get("model")),
                "search_name": clean(identity.get("search_name")),
                "title": clean(product.get("title")),
            }

    live_key = build_model_key(
        brand=brand,
        model=model,
        search_name=search_name,
        title=title,
    )

    if not live_key:
        return None

    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for product, identity in identities:
        catalog_key = build_model_key(
            brand=identity.get("brand"),
            model=identity.get("model"),
            search_name=identity.get("search_name"),
            title=product.get("title"),
        )

        if catalog_key and catalog_key == live_key:
            matches.append((product, identity))

    if len(matches) != 1:
        return None

    product, identity = matches[0]

    return {
        "match_mode": "brand_model",
        "product_id": clean(identity.get("product_id")),
        "asin": clean(identity.get("asin")),
        "brand": clean(identity.get("brand")),
        "model": clean(identity.get("model")),
        "search_name": clean(identity.get("search_name")),
        "title": clean(product.get("title")),
    }
