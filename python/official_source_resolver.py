#!/usr/bin/env python3
"""
Coupon World Official Source Resolver v3.0

Safely finds candidate official manufacturer pages.
It does not approve or publish product knowledge automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient
from resolver_engine import compare_identity


ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = ROOT / "data" / "research_queue.json"
OUTPUT_FILE = ROOT / "data" / "research_results.json"
MIN_MODEL_SCORE = 0.70


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
    "nothing": ["in.nothing.tech", "nothing.tech"],
    "asus": ["asus.com"],
    "sony": ["sony.co.in", "sony.com"],
    "dell": ["dell.com"],
    "jbl": ["in.jbl.com", "jbl.com"],
    "philips": ["philips.co.in", "philips.com"],
    "puma": ["in.puma.com", "puma.com"],
    "mi": ["mi.com", "xiaomi.com"],
    "fire-boltt": ["fireboltt.com"],
    "fireboltt": ["fireboltt.com"],
    "milton": ["milton.in"],
    "hp": ["hp.com"],
    "amazon": ["amazon.in", "amazon.com"],
    "echo": ["amazon.in", "amazon.com"],
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



MODEL_MODIFIERS = {
    "pro",
    "plus",
    "ultra",
    "lite",
    "max",
    "mini",
    "neo",
    "se",
    "fe",
    "prime",
    "advance",
    "advanced",
}


def normalized_model_tokens(value: str) -> set[str]:
    """
    Return comparable model tokens across joined and spaced forms.

    Examples:
    Air8   -> {"air", "8"}
    Air 8  -> {"air", "8"}
    MK240  -> {"mk", "240"}
    17e    -> {"17", "e"}
    """

    text = normalize_text(value)

    # Split letter-number and number-letter boundaries.
    text = re.sub(r"(?<=[a-z])(?=[0-9])", " ", text)
    text = re.sub(r"(?<=[0-9])(?=[a-z])", " ", text)

    tokens = re.findall(r"[a-z0-9]+", text)

    return {
        token
        for token in tokens
        if (
            token not in STOP_WORDS
            and (
                len(token) >= 2
                or token.isdigit()
                or token in {"x", "s", "e"}
            )
        )
    }


def has_extra_model_modifier(
    expected: str,
    candidate: str,
) -> bool:
    """Reject candidate-only model modifiers such as Pro, Lite or Ultra."""

    expected_tokens = normalized_model_tokens(expected)
    candidate_tokens = normalized_model_tokens(candidate)

    extra_modifiers = (
        candidate_tokens
        .difference(expected_tokens)
        .intersection(MODEL_MODIFIERS)
    )

    return bool(extra_modifiers)


def significant_tokens(value: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", normalize_text(value))

    return {
        token
        for token in tokens
        if len(token) >= 2 and token not in STOP_WORDS
    }


def token_match_score(expected: str, candidate: str) -> float:
    expected_tokens = normalized_model_tokens(expected)
    candidate_tokens = normalized_model_tokens(candidate)

    if not expected_tokens or not candidate_tokens:
        return 0.0

    if has_extra_model_modifier(expected, candidate):
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


def is_unwanted_page(url: str) -> bool:
    """
    Reject pages that may be hosted on an official domain but are not
    authoritative product/specification pages.
    """

    lowered = str(url or "").lower()

    unwanted_fragments = (
        "youtube.com",
        "youtu.be",
        "apps.apple.com",
        "play.google.com",
        "/newsroom/",
        "/press-release",
        "/blog/",
        "/community/",
        "/post-details/",
        "/terms",
        "/pre-order-offer",
        "/pages/pre-order",
        "c.realme.com/",
    )

    return any(
        fragment in lowered
        for fragment in unwanted_fragments
    )


def page_type_score(url: str) -> int:
    """
    Prefer technical specification and canonical product pages over
    buy/configuration and support pages.
    """

    lowered = str(url or "").lower()

    if (
        "/specs" in lowered
        or "/specifications" in lowered
        or "/technical-specifications" in lowered
        or "/tech-specs" in lowered
    ):
        return 100

    if "/products/" in lowered:
        return 90

    if "/product/" in lowered:
        return 80

    if "/shop/" in lowered or "/buy-" in lowered:
        return 30

    if "/support/" in lowered or "support." in lowered:
        return 20

    if "/hc/" in lowered:
        return 10

    return 40



def classify_source_type(url: str) -> str:
    """Classify an official source by URL pattern."""

    lowered = str(url or "").lower()

    if lowered.endswith(".pdf") or ".pdf?" in lowered:
        return "pdf"

    if any(
        token in lowered
        for token in (
            "/manual",
            "/manuals",
            "/user-guide",
            "/user-guides",
            "/guide/",
            "/guides/",
        )
    ):
        return "manual"

    if any(
        token in lowered
        for token in (
            "/specs",
            "/specifications",
            "/technical-specifications",
            "/tech-specs",
        )
    ):
        return "specifications"

    if any(
        token in lowered
        for token in (
            "/support/",
            "support.",
            "/hc/",
            "/help/",
        )
    ):
        return "support"

    if any(
        token in lowered
        for token in (
            "/download",
            "/downloads",
            "/drivers",
            "/software",
        )
    ):
        return "downloads"

    if any(
        token in lowered
        for token in (
            "/products/",
            "/product/",
            "/shop/",
            "/buy-",
            "/more-products/",
        )
    ):
        return "product"

    return "official_page"


def build_source_queries(
    brand: str,
    query_core: str,
) -> list[str]:
    """Build brand-agnostic official source discovery queries."""

    base = f"{brand} {query_core}".strip()

    queries = [
        f"{base} official specifications",
        f"{base} official technical specifications",
        f"{base} official product page",
        f"{base} official support",
        f"{base} official manual pdf",
        f"{base} official downloads",
        f"{base} official",
    ]

    seen: set[str] = set()
    unique: list[str] = []

    for query in queries:
        normalized = " ".join(query.split())

        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            unique.append(normalized)

    return unique


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
        "identity_score": 0,
        "identity_decision": None,
        "identity_reasons": [],
        "verified": False,
        "status": "pending",
        "reason": None,
        "candidates": [],
    }

    if not allowed_domains:
        base_result["status"] = "manual_review"
        base_result["reason"] = (
            "No approved official-domain mapping for this brand"
        )
        return base_result

    query_core = core_title

    normalized_core = normalize_brand(core_title)

    if brand_key and normalized_core.startswith(brand_key):
        query_core = re.sub(
            rf"^\s*{re.escape(brand)}\s*",
            "",
            core_title,
            count=1,
            flags=re.I,
        ).strip()

    query_variants = build_source_queries(
        brand,
        query_core,
    )

    base_result["query"] = query_variants[0]
    base_result["query_variants"] = query_variants

    merged_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for query in query_variants:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=7,
            include_domains=allowed_domains,
        )

        for result in response.get("results", []):
            result_url = str(result.get("url") or "").strip()

            if not result_url or result_url in seen_urls:
                continue

            seen_urls.add(result_url)
            merged_results.append(result)

    valid_candidates: list[dict[str, Any]] = []

    for result in merged_results:
        result_title = str(result.get("title") or "").strip()
        result_url = str(result.get("url") or "").strip()

        if not hostname_matches(result_url, allowed_domains):
            continue

        if is_unwanted_page(result_url):
            continue

        model_score = token_match_score(
            core_title,
            result_title,
        )

        # Reject pages that match only a generic number or weak series token.
        # Example: Nothing Ear (3) must not match Nothing Phone (3).
        if model_score < MIN_MODEL_SCORE:
            continue

        tavily_score = float(result.get("score") or 0)

        combined_score = round(
            (model_score * 0.8) + (tavily_score * 0.2),
            4,
        )

        identity = compare_identity(
            expected_text=core_title,
            candidate_title=result_title,
            candidate_url=result_url,
            expected_brand=brand,
        )

        if identity.decision == "reject":
            continue

        valid_candidates.append(
            {
                "title": result_title,
                "url": result_url,
                "model_score": round(model_score, 4),
                "search_score": round(tavily_score, 4),
                "combined_score": combined_score,
                "identity_score": identity.score,
                "identity_decision": identity.decision,
                "identity_reasons": identity.reasons,
                "page_type_score": page_type_score(result_url),
                "source_type": classify_source_type(result_url),
            }
        )

    valid_candidates.sort(
        key=lambda item: (
            item.get("page_type_score", 0),
            item.get("identity_score", 0),
            item.get("combined_score", 0),
        ),
        reverse=True,
    )

    base_result["candidates"] = valid_candidates[:10]
    base_result["source_candidates"] = {
        source_type: [
            candidate
            for candidate in valid_candidates
            if candidate.get("source_type") == source_type
        ][:5]
        for source_type in (
            "specifications",
            "product",
            "support",
            "manual",
            "pdf",
            "downloads",
            "official_page",
        )
        if any(
            candidate.get("source_type") == source_type
            for candidate in valid_candidates
        )
    }

    if not valid_candidates:
        base_result["status"] = "not_found"
        base_result["reason"] = (
            "No result passed official-domain and identity validation"
        )
        return base_result

    preferred_order = {
        "specifications": 7,
        "product": 6,
        "manual": 5,
        "pdf": 5,
        "support": 4,
        "downloads": 3,
        "official_page": 2,
    }

    best = max(
        valid_candidates,
        key=lambda item: (
            preferred_order.get(
                str(item.get("source_type") or ""),
                0,
            ),
            item.get("identity_score", 0),
            item.get("combined_score", 0),
        ),
    )

    base_result["official_title"] = best["title"]
    base_result["official_url"] = best["url"]
    base_result["match_score"] = best["combined_score"]
    base_result["identity_score"] = best["identity_score"]
    base_result["identity_decision"] = best["identity_decision"]
    base_result["identity_reasons"] = best["identity_reasons"]

    if (
        best["identity_decision"] == "verified"
        and best["combined_score"] >= 0.70
    ):
        base_result["verified"] = True
        base_result["status"] = "candidate_verified"
        base_result["reason"] = (
            "Official domain, model identity and search relevance matched"
        )
    else:
        base_result["status"] = "manual_review"
        base_result["reason"] = (
            "Official candidate found, but identity requires manual review"
        )

    return base_result



LOCALE_SEGMENT_PATTERN = re.compile(
    r"^[a-z]{2,3}(?:-[a-z]{2,4})?$",
    re.IGNORECASE,
)


def source_family_key(url: str) -> tuple[str, str]:
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return ("", "")

    hostname = (parsed.hostname or "").lower()

    segments = [
        segment
        for segment in (parsed.path or "").split("/")
        if segment
    ]

    if (
        len(segments) >= 2
        and LOCALE_SEGMENT_PATTERN.fullmatch(segments[0])
    ):
        segments = segments[1:]

    normalized_path = "/" + "/".join(
        segment.lower()
        for segment in segments
    )

    return (
        hostname,
        normalized_path.rstrip("/"),
    )


def stabilize_verified_source(
    previous: dict[str, Any] | None,
    resolved: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(previous, dict):
        return resolved

    if previous.get("verified") is not True:
        return resolved

    if resolved.get("verified") is not True:
        return resolved

    previous_url = str(
        previous.get("official_url") or ""
    ).strip()

    resolved_url = str(
        resolved.get("official_url") or ""
    ).strip()

    if not previous_url or not resolved_url:
        return resolved

    previous_family = source_family_key(previous_url)
    resolved_family = source_family_key(resolved_url)

    if (
        not previous_family[0]
        or previous_family != resolved_family
    ):
        return resolved

    previous_identity = int(
        previous.get("identity_score") or 0
    )

    resolved_identity = int(
        resolved.get("identity_score") or 0
    )

    if resolved_identity >= previous_identity + 15:
        return resolved

    stabilized = dict(resolved)

    stabilized["discovered_official_url"] = resolved_url
    stabilized["discovered_official_title"] = resolved.get(
        "official_title"
    )

    stabilized["official_url"] = previous_url
    stabilized["official_title"] = previous.get(
        "official_title"
    ) or resolved.get("official_title")

    stabilized["source_stability"] = {
        "status": "retained_previous_verified_member",
        "source_family": {
            "hostname": previous_family[0],
            "normalized_path": previous_family[1],
        },
        "previous_url": previous_url,
        "newly_discovered_url": resolved_url,
    }

    return stabilized


def load_existing_results() -> dict[str, dict[str, Any]]:
    if not OUTPUT_FILE.exists():
        return {}

    try:
        payload = load_json(OUTPUT_FILE)
    except (FileNotFoundError, ValueError, OSError):
        return {}

    products = payload.get("products", [])

    if not isinstance(products, list):
        return {}

    return {
        str(item.get("product_id")): item
        for item in products
        if isinstance(item, dict)
        and item.get("product_id") not in (None, "")
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve official product sources from the research queue"
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "status"),
        default="status",
        help="Show status or run a controlled resolver batch",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of selected products to process",
    )

    parser.add_argument(
        "--product-id",
        action="append",
        default=[],
        help="Process a specific product ID; may be repeated",
    )

    parser.add_argument(
        "--pending",
        action="store_true",
        help="Process pending queue products not already resolved",
    )

    return parser


def show_status(
    queue_products: list[dict[str, Any]],
    existing_results: dict[str, dict[str, Any]],
) -> int:
    from collections import Counter

    queue_statuses = Counter(
        str(item.get("status") or "missing")
        for item in queue_products
        if isinstance(item, dict)
    )

    result_statuses = Counter(
        str(item.get("status") or "missing")
        for item in existing_results.values()
    )

    pending_unresolved = sum(
        1
        for item in queue_products
        if isinstance(item, dict)
        and str(item.get("status") or "pending") == "pending"
        and str(item.get("product_id")) not in existing_results
    )

    print("=" * 64)
    print("OFFICIAL SOURCE RESOLVER v4.0 - STATUS")
    print("=" * 64)
    print("Queue products       :", len(queue_products))
    print("Existing results     :", len(existing_results))
    print("Pending unresolved   :", pending_unresolved)
    print("Queue statuses       :", dict(queue_statuses))
    print("Result statuses      :", dict(result_statuses))
    print("=" * 64)
    return 0


def select_products(
    queue_products: list[dict[str, Any]],
    existing_results: dict[str, dict[str, Any]],
    product_ids: list[str],
    pending: bool,
    limit: int,
) -> list[dict[str, Any]]:
    requested_ids = {
        str(product_id).strip()
        for product_id in product_ids
        if str(product_id).strip()
    }

    selected: list[dict[str, Any]] = []

    for product in queue_products:
        if not isinstance(product, dict):
            continue

        product_id = str(product.get("product_id") or "").strip()

        if requested_ids:
            if product_id not in requested_ids:
                continue
        elif pending:
            if str(product.get("status") or "pending") != "pending":
                continue

            if product_id in existing_results:
                continue
        else:
            continue

        selected.append(product)

    if limit > 0:
        selected = selected[:limit]

    return selected


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        queue_payload = load_json(QUEUE_FILE)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"ERROR: {error}")
        return 1

    queue_products = queue_payload.get("products", [])

    if not isinstance(queue_products, list):
        print("ERROR: research_queue.json products must be a list")
        return 1

    existing_results = load_existing_results()

    if args.command == "status":
        return show_status(queue_products, existing_results)

    selected_products = select_products(
        queue_products,
        existing_results,
        args.product_id,
        args.pending,
        args.limit,
    )

    if not selected_products:
        print("No products selected.")
        print("Use --product-id ID or --pending with an optional --limit.")
        return 0

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("ERROR: TAVILY_API_KEY is not configured")
        return 1

    client = TavilyClient(api_key=api_key)
    updated_results = dict(existing_results)

    print("=" * 64)
    print("OFFICIAL SOURCE RESOLVER v4.0")
    print("=" * 64)
    print("Selected products :", len(selected_products))
    print("Existing results  :", len(existing_results))
    print("=" * 64)

    for position, product in enumerate(selected_products, start=1):
        product_id = str(product.get("product_id") or "")
        title = product.get("title")

        print()
        print(f"[{position}/{len(selected_products)}] {product_id} | {title}")

        try:
            resolved = resolve_product(client, product)
        except Exception as error:
            resolved = {
                "product_id": product_id,
                "title": title,
                "verified": False,
                "status": "error",
                "reason": str(error),
            }

        resolved["resolved_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        previous_result = existing_results.get(product_id)

        resolved = stabilize_verified_source(
            previous_result,
            resolved,
        )

        updated_results[product_id] = resolved

        print("Status   :", resolved.get("status"))
        print("URL      :", resolved.get("official_url"))
        print("Score    :", resolved.get("match_score"))
        print("Identity :", resolved.get("identity_score"))
        print("Decision :", resolved.get("identity_decision"))

        stability = resolved.get("source_stability", {})

        if isinstance(stability, dict) and stability.get("status"):
            print("Stability:", stability.get("status"))
            print(
                "Discovered:",
                resolved.get("discovered_official_url"),
            )

    final_products = list(updated_results.values())

    output = {
        "schema_version": "4.0",
        "mode": "incremental",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "products_requested": len(selected_products),
        "total_results": len(final_products),
        "products": final_products,
    }

    save_json(OUTPUT_FILE, output)

    verified_count = sum(
        1
        for item in selected_products
        if updated_results.get(
            str(item.get("product_id")),
            {},
        ).get("verified") is True
    )

    print()
    print("=" * 64)
    print("RESOLVER BATCH COMPLETE")
    print("=" * 64)
    print("Processed       :", len(selected_products))
    print("Verified        :", verified_count)
    print("Needs review    :", len(selected_products) - verified_count)
    print("Total results   :", len(final_products))
    print("Output          :", OUTPUT_FILE)
    print("=" * 64)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
