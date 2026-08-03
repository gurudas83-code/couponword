#!/usr/bin/env python3
"""
Coupon World Official Source Resolver v2.0

Safely finds candidate official manufacturer pages.
It does not approve or publish product knowledge automatically.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient


ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = ROOT / "data" / "research_queue.json"
OUTPUT_FILE = ROOT / "data" / "research_results.json"


BRAND_DOMAINS: dict[str, list[str]] = {
    "redmi": ["mi.com", "xiaomi.com"],
    "xiaomi": ["mi.com", "xiaomi.com"],
    "realme": ["realme.com"],
    "apple": ["apple.com"],
    "samsung": ["samsung.com"],
    "boat": ["boat-lifestyle.com"],
    "noise": ["gonoise.com"],
    "oneplus": ["oneplus.in", "oneplus.com"],
    "logitech": ["logitech.com"],
    "yamaha": ["yamaha.com"],
    "nutrilite": ["amway.in", "amway.com"],
    "amway": ["amway.in", "amway.com"],
}


# Known useful pilot products from the current database.
PILOT_PRODUCT_IDS = {
    "10",  # Redmi 13 5G
    "11",  # realme Buds Air 8
    "13",  # Yamaha PSS-E30
    "14",  # Apple iPhone
    "56",  # Logitech MK240
}


STOP_WORDS = {
    "official",
    "specification",
    "specifications",
    "specs",
    "features",
    "with",
    "and",
    "for",
    "the",
    "of",
    "in",
    "black",
    "blue",
    "white",
    "gold",
    "master",
    "storage",
    "ram",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(f"{path.name} must use UTF-8 encoding") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path.name}: {error}") from error

    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")

    return payload


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def normalize_brand(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def normalize_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^\w\s.+-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def core_product_title(title: str) -> str:
    """
    Remove long marketing details after commas, pipes or brackets.
    Keep enough text to preserve the model identity.
    """

    text = str(title or "").strip()

    # Remove colour/variant text placed inside trailing brackets.
    text = re.sub(r"\([^)]*(colour|color|black|blue|white|gold)[^)]*\)", "", text, flags=re.I)

    # Amazon titles often place feature lists after these separators.
    parts = re.split(r"\s*[|,]\s*", text)

    core = parts[0].strip()

    # Keep useful RAM/storage variant where it is part of the first section.
    return re.sub(r"\s+", " ", core)


def significant_tokens(value: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", normalize_text(value))

    return {
        token
        for token in tokens
        if len(token) >= 2 and token not in STOP_WORDS
    }


def token_match_score(expected: str, candidate: str) -> float:
    expected_tokens = significant_tokens(expected)
    candidate_tokens = significant_tokens(candidate)

    if not expected_tokens or not candidate_tokens:
        return 0.0

    matched = expected_tokens.intersection(candidate_tokens)

    # Coverage of expected model tokens matters more than extra words
    # present in the official page title.
    return len(matched) / len(expected_tokens)


def hostname_matches(url: str, allowed_domains: list[str]) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False

    if not hostname:
        return False

    return any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in allowed_domains
    )


def resolve_product(
    client: TavilyClient,
    product: dict[str, Any],
) -> dict[str, Any]:
    product_id = str(product.get("product_id") or "")
    title = str(product.get("title") or "").strip()
    brand = str(product.get("brand") or "").strip()
    asin = str(product.get("asin") or "").strip()

    brand_key = normalize_brand(brand)
    allowed_domains = BRAND_DOMAINS.get(brand_key, [])

    core_title = core_product_title(title)

    base_result: dict[str, Any] = {
        "product_id": product_id,
        "title": title,
        "brand": brand,
        "asin": asin,
        "core_title": core_title,
        "allowed_domains": allowed_domains,
        "query": None,
        "official_title": None,
        "official_url": None,
        "match_score": 0.0,
        "verified": False,
        "status": "pending",
        "reason": None,
        "candidates": [],
    }

    if not allowed_domains:
        base_result["status"] = "manual_review"
        base_result["reason"] = "No approved official-domain mapping for this brand"
        return base_result

    query = f"{brand} {core_title} official specifications"
    base_result["query"] = query

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=7,
        include_domains=allowed_domains,
    )

    valid_candidates: list[dict[str, Any]] = []

    for result in response.get("results", []):
        result_title = str(result.get("title") or "").strip()
        result_url = str(result.get("url") or "").strip()

        # Tavily result must still pass our own strict hostname check.
        if not hostname_matches(result_url, allowed_domains):
            continue

        model_score = token_match_score(core_title, result_title)
        tavily_score = float(result.get("score") or 0)

        # Model identity is more important than Tavily relevance.
        combined_score = round(
            (model_score * 0.8) + (tavily_score * 0.2),
            4,
        )

        valid_candidates.append(
            {
                "title": result_title,
                "url": result_url,
                "model_score": round(model_score, 4),
                "search_score": round(tavily_score, 4),
                "combined_score": combined_score,
            }
        )

    valid_candidates.sort(
        key=lambda item: item["combined_score"],
        reverse=True,
    )

    base_result["candidates"] = valid_candidates[:5]

    if not valid_candidates:
        base_result["status"] = "not_found"
        base_result["reason"] = "No result passed official-domain validation"
        return base_result

    best = valid_candidates[0]

    base_result["official_title"] = best["title"]
    base_result["official_url"] = best["url"]
    base_result["match_score"] = best["combined_score"]

    # Do not treat moderate or ambiguous candidates as verified.
    if best["model_score"] >= 0.70 and best["combined_score"] >= 0.70:
        base_result["verified"] = True
        base_result["status"] = "candidate_verified"
        base_result["reason"] = "Official domain and model tokens matched"
    else:
        base_result["status"] = "manual_review"
        base_result["reason"] = "Official domain found but model match is not strong enough"

    return base_result


def main() -> int:
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("ERROR: TAVILY_API_KEY is not configured")
        return 1

    try:
        queue_payload = load_json(QUEUE_FILE)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"ERROR: {error}")
        return 1

    queue_products = queue_payload.get("products", [])

    if not isinstance(queue_products, list):
        print("ERROR: research_queue.json products must be a list")
        return 1

    pilot_products = [
        product
        for product in queue_products
        if (
            isinstance(product, dict)
            and str(product.get("product_id")) in PILOT_PRODUCT_IDS
        )
    ]

    client = TavilyClient(api_key=api_key)

    resolved_products: list[dict[str, Any]] = []

    for product in pilot_products:
        print("\n" + "=" * 64)
        print("Researching:", product.get("title"))
        print("=" * 64)

        try:
            resolved = resolve_product(client, product)
        except Exception as error:
            resolved = {
                "product_id": str(product.get("product_id") or ""),
                "title": product.get("title"),
                "verified": False,
                "status": "error",
                "reason": str(error),
            }

        resolved_products.append(resolved)

        print("Status :", resolved.get("status"))
        print("URL    :", resolved.get("official_url"))
        print("Score  :", resolved.get("match_score"))

    output = {
        "schema_version": "2.0",
        "mode": "pilot",
        "products_requested": len(pilot_products),
        "products": resolved_products,
    }

    save_json(OUTPUT_FILE, output)

    verified_count = sum(
        1 for item in resolved_products if item.get("verified") is True
    )

    print("\n" + "=" * 64)
    print("OFFICIAL SOURCE RESOLVER v2.0")
    print("=" * 64)
    print("Pilot products :", len(pilot_products))
    print("Verified       :", verified_count)
    print("Manual review  :", len(pilot_products) - verified_count)
    print("Output         :", OUTPUT_FILE)
    print("=" * 64)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())