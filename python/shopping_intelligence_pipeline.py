#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Intelligence Pipeline v1.1

One command:
    py python/shopping_intelligence_pipeline.py --query "..."

v1.1 fixes the v1.0 bottleneck where market discovery and identity succeeded
but official verification returned zero candidates.

Main changes:
- Cleans commerce-style result titles before identity parsing.
- Recovers known brands from the title using the resolver's own BRAND_DOMAINS.
- Uses the existing strict resolver first.
- If the strict resolver cannot proceed because the brand is not registered,
  performs a conservative universal official-source fallback.
- Universal fallback still requires resolver_engine.compare_identity() == verified.
- Prints grouped failure diagnostics in the same run.
- Does not auto-publish or mutate permanent product knowledge.
"""

from __future__ import annotations
import time

import argparse
import ast
import inspect
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from intent_engine import parse_query
from market_discovery import discover_market
from official_source_resolver import (
    BRAND_DOMAINS,
    normalize_brand,
    resolve_product,
)
from official_spec_extractor import extract_one
from product_fit_signal_builder import build_fit_signals
from product_evidence_store import (
    find_verified_evidence,
    save_verified_evidence,
)
from product_identity_v2 import build_identity
from retail_price_evidence import build_price_evidence
from resolver_engine import compare_identity
from weighted_fit_engine import calculate_product_fit


RUNTIME_OUTPUT = ROOT / "data" / "runtime_shopping_intelligence.json"

MIN_FIT_PERCENT = 50
DEFAULT_MAX_RESULTS = 5
DEFAULT_MIN_RESULTS = 3

GENERIC_LEADING_WORDS = {
    "buy", "shop", "get", "order", "latest", "new", "sale",
    "best", "online", "india", "official",
}

GENERIC_BRANDS = {
    "", "buy", "shop", "get", "order", "latest", "new",
    "sale", "best", "online", "earbuds", "headphones",
    "smartphone", "phone", "mobile", "laptop",
}

NON_OFFICIAL_HOST_FRAGMENTS = (
    "amazon.",
    "flipkart.",
    "croma.",
    "reliancedigital.",
    "vijaysales.",
    "smartprix.",
    "91mobiles.",
    "gadgets360.",
    "indiatoday.",
    "timesofindia.",
    "youtube.",
    "facebook.",
    "instagram.",
    "reddit.",
    "pinterest.",
    "wikipedia.",
    "gsmarena.",
)

NON_OFFICIAL_PATH_FRAGMENTS = (
    "/blog/",
    "/blogs/",
    "/news/",
    "/review/",
    "/reviews/",
    "/guide/",
    "/guides/",
    "/article/",
    "/articles/",
    "/community/",
    "/forum/",
)

OFFICIAL_PAGE_HINTS = (
    "/product/",
    "/products/",
    "/spec",
    "/specs",
    "/specifications",
    "/support/",
    "/shop/",
    "/buy-",
    "/more-products/",
    "/headphones/",
    "/earbuds/",
    "/smartphones/",
    "/phones/",
    "/laptops/",
)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def hostname(url: str) -> str:
    try:
        return (urlparse(clean(url)).hostname or "").lower()
    except ValueError:
        return ""


def sanitize_discovery_title(value: Any) -> str:
    title = clean(value)
    title = re.sub(r"\s*\.\.\.\s*$", "", title)

    # Remove marketplace verbs that poison brand detection:
    # "Buy boAt Airdopes..." -> "boAt Airdopes..."
    words = title.split()
    while words and words[0].lower().strip(":-|") in GENERIC_LEADING_WORDS:
        words.pop(0)

    title = " ".join(words).strip()

    # Remove common source suffixes without destroying hyphenated models.
    for sep in (" | ", " – ", " — "):
        if sep in title:
            left = clean(title.split(sep, 1)[0])
            if len(left.split()) >= 2:
                title = left
                break

    return title


def canonical_brand_from_title(title: str) -> str:
    normalized_title = re.sub(
        r"[^a-z0-9]+",
        " ",
        title.lower(),
    ).strip()

    # Samsung Galaxy smartphone families are sometimes listed without
    # the manufacturer name. Treat Galaxy A/M/F/S/Z model families as
    # Samsung, not as a standalone "Galaxy" brand.
    if re.search(
        r"\bgalaxy\s+(?:a|m|f|s|z)\s*\d",
        normalized_title,
        flags=re.IGNORECASE,
    ):
        return "Samsung"

    # Retailers/platforms may appear in search-result titles but
    # must never become the product manufacturer/brand.
    non_product_brand_keys = {
        "amazon",
        "flipkart",
        "croma",
        "reliance digital",
        "vijay sales",
    }

    matches: list[tuple[int, int, str]] = []

    for brand_key in BRAND_DOMAINS.keys():
        normalized_brand = normalize_brand(brand_key)

        if not normalized_brand:
            continue

        if normalized_brand in non_product_brand_keys:
            continue

        pattern = rf"(?:^|\s){re.escape(normalized_brand)}(?:\s|$)"
        match = re.search(pattern, normalized_title)

        if not match:
            continue

        # Prefer a genuine brand occurring earlier in the product title.
        # Longer aliases win when position is equal.
        matches.append(
            (
                match.start(),
                -len(normalized_brand),
                brand_key,
            )
        )

    if not matches:
        return ""

    matches.sort()

    return matches[0][2]

def fallback_brand_from_title(title: str) -> str:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9.+&'-]*", title)

    for word in words:
        lowered = word.lower()
        if lowered in GENERIC_LEADING_WORDS:
            continue
        if lowered in {
            "wireless", "bluetooth", "earbuds", "earbud", "tws",
            "headphones", "headphone", "with", "for", "and",
        }:
            continue
        if word.isdigit():
            continue
        return word

    return ""


def repair_identity(
    identity: dict[str, Any],
    cleaned_title: str,
) -> dict[str, Any]:
    repaired = dict(identity)

    brand = clean(repaired.get("brand"))
    brand_key = normalize_brand(brand)

    if (
        brand_key == "galaxy"
        or re.search(
            r"\bgalaxy\s+(?:a|m|f|s|z)\s*\d",
            cleaned_title,
            flags=re.IGNORECASE,
        )
    ):
        repaired["brand"] = "Samsung"
        brand = "Samsung"
        brand_key = normalize_brand(brand)

    if brand_key in GENERIC_BRANDS or not brand:
        known = canonical_brand_from_title(cleaned_title)
        repaired["brand"] = known or fallback_brand_from_title(cleaned_title)

    search_name = clean(repaired.get("search_name"))

    if not search_name or search_name.lower().startswith(("buy ", "shop ")):
        repaired["search_name"] = cleaned_title

    # Ensure product/model search remains brand-bearing.
    brand = clean(repaired.get("brand"))
    search_name = clean(repaired.get("search_name"))

    if brand and search_name and normalize_brand(brand) not in normalize_brand(search_name):
        repaired["search_name"] = f"{brand} {search_name}".strip()

    repaired["official_search_query"] = (
        f"{clean(repaired.get('search_name'))} official specifications"
    )

    return repaired


def call_build_identity(
    product: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    signature = inspect.signature(build_identity)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]

    if len(positional) >= 2:
        result = build_identity(product, position)
    else:
        result = build_identity(product)

    if not isinstance(result, dict):
        raise TypeError("build_identity() returned a non-dict result")

    return result


def candidate_to_identity_input(
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    cleaned_title = sanitize_discovery_title(candidate.get("title"))

    return (
        {
            "product_id": clean(candidate.get("candidate_id")),
            "title": cleaned_title,
            "brand": canonical_brand_from_title(cleaned_title),
            "asin": clean(candidate.get("asin")),
            "category": "",
            "link": clean(candidate.get("source_url")),
            "image": clean(candidate.get("search_image")),
            "price": None,
        },
        cleaned_title,
    )


def resolver_input_from_identity(
    candidate: dict[str, Any],
    identity: dict[str, Any],
) -> dict[str, Any]:
    return {
        "product_id": clean(
            identity.get("product_id")
            or candidate.get("candidate_id")
        ),
        "title": clean(
            identity.get("search_name")
            or sanitize_discovery_title(candidate.get("title"))
        ),
        "brand": clean(identity.get("brand")),
        "asin": clean(identity.get("asin")),
    }


def is_possible_official_page(
    url: str,
    expected_brand: str,
) -> bool:
    host = hostname(url)
    lowered = clean(url).lower()

    if not host:
        return False

    if any(fragment in host for fragment in NON_OFFICIAL_HOST_FRAGMENTS):
        return False

    if any(fragment in lowered for fragment in NON_OFFICIAL_PATH_FRAGMENTS):
        return False

    brand_norm = normalize_brand(expected_brand)
    host_norm = re.sub(r"[^a-z0-9]+", "", host)

    brand_in_host = bool(
        brand_norm
        and re.sub(r"[^a-z0-9]+", "", brand_norm) in host_norm
    )

    # Registered brands must resolve only to approved official domains.
    approved_domains = BRAND_DOMAINS.get(brand_norm, [])

    if isinstance(approved_domains, str):
        approved_domains = [approved_domains]

    if approved_domains:
        for domain in approved_domains:
            domain = clean(domain).lower().lstrip("www.")

            if not domain:
                continue

            if host == domain or host.endswith("." + domain):
                return True

        return False

    # For an unregistered brand, brand-name presence in the hostname is
    # required. A merely product-looking path on an unrelated retailer or
    # informational site is not enough to call it official.
    return brand_in_host


def universal_official_resolve(
    client: TavilyClient | None,
    product: dict[str, Any],
    identity: dict[str, Any],
) -> dict[str, Any]:
    product_id = clean(product.get("product_id"))
    title = clean(
        identity.get("search_name")
        or product.get("title")
    )
    brand = clean(
        identity.get("brand")
        or product.get("brand")
    )

    result: dict[str, Any] = {
        "product_id": product_id,
        "title": title,
        "brand": brand,
        "asin": clean(product.get("asin")),
        "core_title": title,
        "allowed_domains": [],
        "query": None,
        "query_variants": [],
        "official_title": None,
        "official_url": None,
        "match_score": 0.0,
        "identity_score": 0,
        "identity_decision": None,
        "identity_reasons": [],
        "verified": False,
        "status": "manual_review",
        "reason": "Universal official-source fallback found no verified source",
        "candidates": [],
        "resolver_mode": "universal_fallback",
    }

    if not brand or normalize_brand(brand) in GENERIC_BRANDS:
        result["reason"] = "Brand identity is not reliable enough for official search"
        return result

    # Tavily is optional. Universal web-search fallback cannot run
    # without a search client, so fail closed instead of crashing.
    if client is None:
        result["status"] = "manual_review"
        result["reason"] = (
            "Universal official-source search unavailable because "
            "no Tavily client is configured"
        )
        return result

    queries = [
        f"{brand} {title} official specifications",
        f"{brand} {title} official product",
        f"{brand} {title} official",
    ]

    seen_query: set[str] = set()
    unique_queries: list[str] = []

    for query in queries:
        q = clean(query)
        if q.lower() not in seen_query:
            seen_query.add(q.lower())
            unique_queries.append(q)

    result["query_variants"] = unique_queries
    result["query"] = unique_queries[0]

    seen_urls: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for query in unique_queries:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=10,
        )

        for item in response.get("results", []):
            if not isinstance(item, dict):
                continue

            candidate_title = clean(item.get("title"))
            candidate_url = clean(item.get("url"))

            if not candidate_title or not candidate_url:
                continue

            if candidate_url in seen_urls:
                continue

            seen_urls.add(candidate_url)

            if not is_possible_official_page(candidate_url, brand):
                continue

            try:
                decision_obj = compare_identity(
                    expected_text=title,
                    candidate_title=candidate_title,
                    candidate_url=candidate_url,
                    expected_brand=brand,
                )
                decision = decision_obj.to_dict()
            except Exception as error:
                decision = {
                    "score": 0,
                    "decision": "reject",
                    "reasons": [f"Identity comparison failed: {error}"],
                }

            score = int(decision.get("score") or 0)
            verdict = clean(decision.get("decision")).lower()
            tavily_score = safe_float(item.get("score")) or 0.0

            candidates.append(
                {
                    "title": candidate_title,
                    "url": candidate_url,
                    "host": hostname(candidate_url),
                    "identity_score": score,
                    "identity_decision": verdict,
                    "identity_reasons": decision.get("reasons", []),
                    "search_score": round(tavily_score, 4),
                    "query": query,
                }
            )

    candidates.sort(
        key=lambda x: (
            x["identity_score"],
            x["search_score"],
        ),
        reverse=True,
    )

    result["candidates"] = candidates[:5]

    verified = [
        item
        for item in candidates
        if item["identity_decision"] == "verified"
        and item["identity_score"] >= 80
    ]

    if not verified:
        if candidates:
            best = candidates[0]
            result["official_title"] = best["title"]
            result["official_url"] = best["url"]
            result["identity_score"] = best["identity_score"]
            result["identity_decision"] = best["identity_decision"]
            result["identity_reasons"] = best["identity_reasons"]
            result["match_score"] = round(best["identity_score"] / 100, 4)
            result["reason"] = (
                "Official-looking source found but identity did not pass "
                "the strict verified threshold"
            )
        return result

    best = verified[0]
    result["official_title"] = best["title"]
    result["official_url"] = best["url"]
    result["identity_score"] = best["identity_score"]
    result["identity_decision"] = best["identity_decision"]
    result["identity_reasons"] = best["identity_reasons"]
    result["match_score"] = round(best["identity_score"] / 100, 4)
    result["verified"] = True
    result["status"] = "candidate_verified"
    result["reason"] = (
        "Universal official-source search passed strict identity verification"
    )

    return result


def resolve_with_fallback(
    client: TavilyClient | None,
    candidate: dict[str, Any],
    identity: dict[str, Any],
) -> dict[str, Any]:
    product = resolver_input_from_identity(candidate, identity)

    primary: dict[str, Any]

    try:
        primary = resolve_product(client, product)
    except Exception as error:
        primary = {
            "product_id": product["product_id"],
            "title": product["title"],
            "brand": product["brand"],
            "verified": False,
            "status": "error",
            "reason": str(error),
        }

    primary["resolver_mode"] = "registered_domain"

    if primary.get("verified") is True:
        return primary

    reason = clean(primary.get("reason")).lower()
    status = clean(primary.get("status")).lower()

    fallback_needed = (
        "no approved official-domain mapping" in reason
        or status in {"not_found", "manual_review", "error"}
    )

    if not fallback_needed:
        return primary

    fallback = universal_official_resolve(
        client,
        product,
        identity,
    )

    # Preserve why the strict path failed.
    fallback["primary_resolver_status"] = primary.get("status")
    fallback["primary_resolver_reason"] = primary.get("reason")

    return fallback


def extraction_is_usable(
    extraction: dict[str, Any],
) -> tuple[bool, str]:
    if extraction.get("fetch_status") != "success":
        return False, clean(
            extraction.get("review", {}).get("reason")
            or extraction.get("fetch_status")
            or "Extraction did not succeed"
        )

    if extraction.get("resolver_verified") is not True:
        return False, "Official source was not resolver-verified"

    review = extraction.get("review", {})
    review_status = clean(review.get("status")).lower()

    if review_status in {"rejected", "rejected_candidate", "error"}:
        return False, clean(
            review.get("reason")
            or "Extractor rejected the official-page candidate"
        )

    page_identity = safe_float(extraction.get("page_identity_score"))

    if page_identity is not None and page_identity < 0.50:
        return False, (
            f"Official page identity score too low: {page_identity:.2f}"
        )

    specs = extraction.get("specifications")
    features = extraction.get("features")

    spec_count = len(specs) if isinstance(specs, dict) else 0
    feature_count = len(features) if isinstance(features, list) else 0

    if spec_count == 0 and feature_count == 0:
        return False, "No usable specification/feature evidence extracted"

    return True, ""




def normalize_feature_corpus(values: Any) -> list[str]:
    """
    Canonical runtime feature representation.

    Rules:
    - structured evidence dict -> text/value/label only
    - Python-stringified evidence dict -> safely parse, then text only
    - metadata such as confidence/source/relevance_score is discarded
    - blank values are removed
    - case-insensitive duplicates are removed
    - output is always list[str]
    """
    if not isinstance(values, list):
        values = [values] if values not in (None, "") else []

    output: list[str] = []
    seen: set[str] = set()

    for item in values:
        value = ""

        if isinstance(item, dict):
            for key in ("text", "value", "label"):
                candidate = item.get(key)

                if candidate not in (None, ""):
                    value = clean(candidate)
                    break

        elif isinstance(item, str):
            stripped = item.strip()
            parsed = None

            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    parsed = ast.literal_eval(stripped)
                except (ValueError, SyntaxError):
                    parsed = None

            if isinstance(parsed, dict):
                for key in ("text", "value", "label"):
                    candidate = parsed.get(key)

                    if candidate not in (None, ""):
                        value = clean(candidate)
                        break
            else:
                value = clean(item)

        else:
            value = clean(item)

        if not value:
            continue

        key = value.casefold()

        if key in seen:
            continue

        seen.add(key)
        output.append(value)

    return output


def enrich_priority_evidence(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    extraction: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any]:
    """
    Consolidate already-verified runtime evidence for dimensions that
    matter most to the shopper.

    Important:
    - No specification is invented.
    - No network request is performed here.
    - Only evidence already present in candidate/extraction is reused.
    - High-priority dimensions are recorded for later diagnostics.
    """
    enriched = dict(profile)

    features = list(enriched.get("features") or [])
    attributes = dict(enriched.get("attributes") or {})

    weights = intent.get("priority_weights") or {}

    priority_dimensions = [
        str(name)
        for name, weight in sorted(
            weights.items(),
            key=lambda item: int(item[1] or 0),
            reverse=True,
        )
        if int(weight or 0) >= 15
    ]

    evidence_parts: list[str] = []

    def evidence_text(value: Any) -> str:
        """
        Convert verified evidence to human-readable text only.

        Extraction features may be structured dictionaries such as:
        {
            "text": "Battery Capacity (mAh, Typical) 5000",
            "source": "li",
            "confidence": 77,
            "relevance_score": 1,
        }

        Metadata must never be converted into product evidence.
        """
        if value in (None, ""):
            return ""

        if isinstance(value, dict):
            for key in ("text", "value", "label"):
                candidate = value.get(key)
                if candidate not in (None, ""):
                    return clean(candidate)

            return ""

        return clean(value)

    def add_evidence(value: Any) -> None:
        value = evidence_text(value)

        if value and value not in evidence_parts:
            evidence_parts.append(value)

    # Verified/discovered listing evidence already available in memory.
    add_evidence(candidate.get("source_title"))
    add_evidence(candidate.get("title"))
    add_evidence(candidate.get("snippet"))

    # Evidence produced by official extraction or verified live-fast mode.
    for value in extraction.get("features") or []:
        add_evidence(value)

    specifications = extraction.get("specifications") or {}

    if isinstance(specifications, dict):
        for key, value in specifications.items():
            key_text = clean(key)

            # Structured specification objects must contribute only
            # their human-readable value/text/label. Metadata such as
            # source/confidence must never enter the feature corpus.
            value_text = evidence_text(value)

            if key_text and value_text:
                attributes.setdefault(key_text, value_text)
                add_evidence(f"{key_text}: {value_text}")

    # Add consolidated evidence to the feature corpus consumed by the
    # fit-signal builder. Deduplication keeps the profile bounded.
    for value in evidence_parts:
        if value not in features:
            features.append(value)

    enriched["features"] = normalize_feature_corpus(features)
    enriched["attributes"] = attributes

    enriched["priority_evidence"] = {
        "dimensions": priority_dimensions,
        "threshold": 15,
        "mode": "existing_verified_evidence_only",
        "evidence_items": len(evidence_parts),
    }

    return enriched




def retrieve_missing_priority_evidence(
    profile: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any]:
    """
    Retrieve bounded external evidence only for high-priority criteria
    that remain unknown after the first scoring pass.

    Safety:
    - Search evidence is never used unless product identity matches.
    - Only high-priority unknown dimensions are queried.
    - No missing specification is invented.
    - If Tavily is unavailable, return profile unchanged.
    """
    # Live recommendation requests must not depend on external
    # enrichment. Verified cached/official evidence is sufficient for
    # the first response; unresolved criteria remain unknown and can
    # be enriched later in deep/background mode.
    live_fast = clean(
        os.environ.get("COUPONWORLD_LIVE_FAST", "1")
    ).lower() not in {"0", "false", "no", "off"}

    if live_fast:
        enriched = dict(profile)

        provenance = dict(enriched.get("provenance") or {})
        provenance["priority_evidence_retrieval"] = [{
            "status": "skipped_live_fast",
            "reason": (
                "External priority-evidence retrieval is disabled "
                "on the live-fast recommendation path"
            ),
        }]
        enriched["provenance"] = provenance

        return enriched

    api_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        return profile

    weights = intent.get("priority_weights") or {}

    # First-pass signals tell us what is genuinely missing.
    initial_signals = build_fit_signals(profile, intent)

    # Only criteria for which this retriever has an evidence-search
    # strategy are eligible for the bounded live pass.
    #
    # Do not use an arbitrary minimum-weight threshold here. Category
    # defaults may assign important dimensions (for example phone
    # performance/software support) weights below 15, which previously
    # prevented those unknown signals from ever reaching retrieval.
    query_terms = {
        "battery": "battery capacity charging",
        "camera": "camera OIS ultrawide telephoto",
        "display": "display panel refresh rate brightness",
        "performance": "processor chipset performance",
        "software_support": "software updates support years",
        "connectivity": "5G WiFi Bluetooth NFC",
        "ram": "RAM memory",
        "storage": "storage capacity",
    }

    missing: list[str] = []

    for dimension, weight in sorted(
        weights.items(),
        key=lambda item: int(item[1] or 0),
        reverse=True,
    ):
        dimension = str(dimension)

        # Unsupported/generic criteria such as ease_of_use must not
        # consume one of the limited retrieval slots.
        if dimension not in query_terms:
            continue

        signal_obj = initial_signals.get(dimension)

        if not isinstance(signal_obj, dict):
            continue

        if signal_obj.get("match") is None:
            missing.append(dimension)

    if not missing:
        return profile

    # Keep live latency bounded. Filtering supported dimensions before
    # truncation ensures that an unsupported criterion cannot steal a
    # retrieval slot.
    missing = missing[:2]

    title = clean(profile.get("title"))
    brand = clean(profile.get("brand"))

    if not title:
        return profile

    client = TavilyClient(api_key=api_key)

    existing_features = normalize_feature_corpus(
        profile.get("features") or []
    )
    enrichment_records: list[dict[str, Any]] = []

    for dimension in missing:
        terms = query_terms.get(dimension)

        if not terms:
            continue

        query = f"{brand} {title} {terms}".strip()

        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=4,
            )
        except Exception as error:
            enrichment_records.append({
                "criterion": dimension,
                "query": query,
                "status": "search_failed",
                "reason": str(error),
            })
            continue

        for result in response.get("results", []):
            if not isinstance(result, dict):
                continue

            result_title = clean(result.get("title"))
            result_url = clean(result.get("url"))
            result_content = clean(result.get("content"))

            if not result_title or not result_content:
                continue

            try:
                identity_obj = compare_identity(
                    expected_text=title,
                    candidate_title=result_title,
                    candidate_url=result_url,
                    expected_brand=brand,
                )
                identity_check = identity_obj.to_dict()
            except Exception:
                continue

            if clean(identity_check.get("decision")).lower() != "verified":
                continue

            evidence_text = clean(
                f"{result_title}. {result_content}"
            )

            if evidence_text and evidence_text not in existing_features:
                existing_features.append(evidence_text)

            enrichment_records.append({
                "criterion": dimension,
                "query": query,
                "source_url": result_url,
                "source_title": result_title,
                "identity_score": identity_check.get("score"),
            })

            # One verified identity-bound source per criterion is enough
            # for this bounded live pass.
            break

    enriched = dict(profile)
    enriched["features"] = normalize_feature_corpus(
        existing_features
    )

    provenance = dict(enriched.get("provenance") or {})
    provenance["priority_evidence_retrieval"] = enrichment_records
    enriched["provenance"] = provenance

    return enriched



def runtime_profile_from_extraction(
    *,
    candidate: dict[str, Any],
    identity: dict[str, Any],
    resolved: dict[str, Any],
    extraction: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any]:
    specifications = extraction.get("specifications", {})
    if not isinstance(specifications, dict):
        specifications = {}

    features = extraction.get("features", [])
    if not isinstance(features, list):
        features = []

    # Normalize and deduplicate extraction features at the runtime
    # profile boundary. This also cleans stale cached evidence that may
    # contain Python-stringified feature dictionaries.
    normalized_features: list[Any] = []
    seen_feature_text: set[str] = set()

    for item in features:
        normalized_item = item
        feature_text = ""

        if isinstance(item, dict):
            for key in ("text", "value", "label"):
                value = item.get(key)
                if value not in (None, ""):
                    feature_text = clean(value)
                    break

        elif isinstance(item, str):
            stripped = item.strip()

            if (
                stripped.startswith("{")
                and stripped.endswith("}")
                and (
                    "'text'" in stripped
                    or '"text"' in stripped
                    or "'value'" in stripped
                    or '"value"' in stripped
                    or "'label'" in stripped
                    or '"label"' in stripped
                )
            ):
                try:
                    import ast
                    parsed = ast.literal_eval(stripped)
                except (ValueError, SyntaxError):
                    parsed = None

                if isinstance(parsed, dict):
                    for key in ("text", "value", "label"):
                        value = parsed.get(key)
                        if value not in (None, ""):
                            feature_text = clean(value)
                            normalized_item = feature_text
                            break
            else:
                feature_text = clean(item)

        else:
            feature_text = clean(item)

        if not feature_text:
            continue

        dedupe_key = feature_text.lower()

        if dedupe_key in seen_feature_text:
            continue

        seen_feature_text.add(dedupe_key)

        # Keep native structured evidence where available; stringified
        # dicts are converted to their human-readable evidence text.
        normalized_features.append(normalized_item)

    features = normalized_features

    existing_commerce_price = resolved.get("commerce_evidence")

    if (
        isinstance(existing_commerce_price, dict)
        and existing_commerce_price.get("verified") is True
        and existing_commerce_price.get("price") is not None
    ):
        price_evidence = existing_commerce_price
    else:
        price_evidence = build_price_evidence(candidate)

    verified_market_price = (
        price_evidence.get("price")
        if price_evidence.get("verified") is True
        else None
    )

    profile: dict[str, Any] = {
        "product_id": clean(
            identity.get("product_id")
            or candidate.get("candidate_id")
        ),
        "title": clean(
            extraction.get("search_name")
            or identity.get("search_name")
            or candidate.get("title")
        ),
        "brand": clean(
            extraction.get("brand")
            or identity.get("brand")
        ),
        "category": clean(intent.get("category")),
        "price": verified_market_price,
        "asin": clean(
            candidate.get("asin")
            or identity.get("asin")
        ),
        "image_url": clean(candidate.get("search_image")),
        "commerce_provider": clean(candidate.get("provider")),
        "attributes": specifications,
        "features": features,
        "best_for": [],
        "limitations": [],
        "official_product_url": clean(resolved.get("official_url")),
        "market_source_url": clean(candidate.get("source_url")),
        "market_source_host": clean(candidate.get("source_host")),
        "discovery_channel": clean(candidate.get("discovery_channel")),
        "provenance": {
            "discovery_url": clean(candidate.get("source_url")),
            "official_url": clean(resolved.get("official_url")),
            "official_title": clean(resolved.get("official_title")),
            "resolver_mode": clean(resolved.get("resolver_mode")),
            "resolver_status": clean(resolved.get("status")),
            "resolver_identity_score": resolved.get("identity_score"),
            "resolver_match_score": resolved.get("match_score"),
            "extractor_page_identity_score": extraction.get(
                "page_identity_score"
            ),
            "extractor_review_status": clean(
                extraction.get("review", {}).get("status")
            ),
            "fetch_status": clean(extraction.get("fetch_status")),
            "price_evidence": price_evidence,
        },
    }

    return profile


def criterion_groups(
    assessment: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    strong: list[str] = []
    tradeoffs: list[str] = []
    unknown: list[str] = []

    for item in assessment.get("criteria", []) or []:
        if not isinstance(item, dict):
            continue

        criterion = clean(item.get("criterion"))
        reason = clean(item.get("reason"))
        match = item.get("match_score")

        if match is None:
            unknown.append(
                f"{criterion}: {reason or 'No reliable evidence'}"
            )
            continue

        score = safe_float(match)

        if score is None:
            unknown.append(f"{criterion}: {reason}")
        elif score >= 0.80:
            strong.append(f"{criterion}: {reason}")
        elif score < 0.50:
            # A low partial score is not automatically a negative.
            # Example: "6.67-inch class display" is valid evidence,
            # but by itself is not a user-facing trade-off.
            negative_terms = (
                "below",
                "missing",
                "not ",
                "no ",
                "poor",
                "weak",
                "low ",
                "slow",
                "limited",
                "unsupported",
                "mismatch",
                "exceeds",
                "over budget",
            )

            reason_lower = reason.lower()

            if any(term in reason_lower for term in negative_terms):
                tradeoffs.append(f"{criterion}: {reason}")

    return strong, tradeoffs, unknown


def run_pipeline(
    query: str,
    max_candidates: int = 15,
    max_results: int = 5,
    live_fast: bool = False,
) -> dict[str, Any]:
    pipeline_started = time.perf_counter()

    intent_started = time.perf_counter()
    intent = parse_query(query)
    intent_seconds = time.perf_counter() - intent_started

    discovery_started = time.perf_counter()
    discovery = discover_market(
        user_query=query,
        max_candidates=max_candidates,
        live_fast=live_fast,
    )
    discovery_seconds = time.perf_counter() - discovery_started

    discovered = [
        item
        for item in discovery.get("candidates", [])
        if isinstance(item, dict)
    ]

    api_key = os.environ.get("TAVILY_API_KEY")

    client = (
        TavilyClient(api_key=api_key)
        if api_key
        else None
    )

    identities: list[dict[str, Any]] = []
    resolver_records: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []
    scored_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    candidate_timings: list[dict[str, Any]] = []

    for position, candidate in enumerate(discovered, start=1):
        candidate_started = time.perf_counter()
        candidate_id = clean(candidate.get("candidate_id"))
        raw_title = clean(candidate.get("title"))

        try:
            identity_input, cleaned_title = candidate_to_identity_input(candidate)
            identity = call_build_identity(identity_input, position)
            identity = repair_identity(identity, cleaned_title)
        except Exception as error:
            failures.append({
                "candidate_id": candidate_id,
                "title": raw_title,
                "stage": "identity",
                "reason": str(error),
            })
            continue

        identities.append(identity)

        # ---------------------------------------------------------
        # EXACT NAMED-MODEL LOCK
        # ---------------------------------------------------------
        # Deep research for an explicitly named model must never
        # drift into a sibling model and persist that sibling's
        # evidence as if it answered the requested model.
        #
        # Examples:
        #   "Samsung Galaxy F36 5G" -> F36 candidates only
        #   "Samsung Galaxy F06 5G" -> reject
        #
        # Generic shopping queries such as:
        #   "Samsung phone under 25000"
        #   "best phone under 20000"
        # remain unrestricted.
        if not live_fast:
            query_key = re.sub(
                r"[^a-z0-9]+",
                " ",
                clean(query).lower(),
            ).strip()

            candidate_key = re.sub(
                r"[^a-z0-9]+",
                " ",
                clean(
                    identity.get("search_name")
                    or identity.get("model")
                    or raw_title
                ).lower(),
            ).strip()

            # Conservative model-token detection.
            # A token must contain both letters and digits:
            # F36, A23, S24, G86, C85, 100x, etc.
            query_model_tokens = {
                token
                for token in query_key.split()
                if re.search(r"[a-z]", token)
                and re.search(r"\d", token)
                and token not in {"5g", "4g", "3g", "2g"}
            }

            if query_model_tokens:
                candidate_tokens = set(candidate_key.split())

                missing_model_tokens = (
                    query_model_tokens - candidate_tokens
                )

                if missing_model_tokens:
                    failures.append({
                        "candidate_id": candidate_id,
                        "title": raw_title,
                        "stage": "exact_model_lock",
                        "status": "rejected",
                        "reason": (
                            "Named-model deep research mismatch: "
                            f"required {sorted(query_model_tokens)}, "
                            f"candidate identity was "
                            f"{identity.get('search_name') or raw_title}"
                        ),
                        "required_model_tokens": sorted(
                            query_model_tokens
                        ),
                    })
                    continue

        if not clean(identity.get("brand")) or not clean(identity.get("search_name")):
            failures.append({
                "candidate_id": candidate_id,
                "title": raw_title,
                "stage": "identity",
                "reason": "Identity missing usable brand or search_name",
            })
            continue

        resolved = None

        # ---------------------------------------------------------
        # LIVE-FAST COMMERCE-FIRST PATH
        # ---------------------------------------------------------
        # For live visitor requests, first try the already discovered
        # retailer listing. If both identity and primary selling price
        # verify independently, avoid the slower official-source
        # resolver on the critical response path.
        #
        # Deep/non-live mode keeps the original resolver-first flow.
        # ---------------------------------------------------------
        if live_fast:
            market_url = clean(candidate.get("source_url"))
            market_title = clean(candidate.get("title") or raw_title)

            try:
                fast_identity_obj = compare_identity(
                    expected_text=clean(
                        identity.get("search_name")
                        or identity.get("model")
                        or raw_title
                    ),
                    candidate_title=market_title,
                    candidate_url=market_url,
                    expected_brand=clean(identity.get("brand")),
                )
                fast_identity = fast_identity_obj.to_dict()
            except Exception as error:
                fast_identity = {
                    "score": 0,
                    "decision": "reject",
                    "reasons": [
                        f"Fast commerce identity comparison failed: {error}"
                    ],
                }

            fast_price = build_price_evidence(candidate)

            fast_commerce_verified = bool(
                clean(fast_identity.get("decision")).lower() == "verified"
                and fast_price.get("verified") is True
                and fast_price.get("price") is not None
            )

            if fast_commerce_verified:
                resolved = {
                    "product_id": clean(
                        identity.get("product_id")
                        or candidate.get("candidate_id")
                    ),
                    "title": market_title,
                    "brand": clean(identity.get("brand")),
                    "verified": True,
                    "status": "commerce_evidence_verified",
                    "resolver_mode": "verified_retailer_fallback",
                    "official_url": market_url,
                    "official_title": market_title,
                    "identity_score": int(
                        fast_identity.get("score") or 0
                    ),
                    "identity_decision": fast_identity.get("decision"),
                    "identity_reasons": fast_identity.get("reasons", []),
                    "match_score": round(
                        int(fast_identity.get("score") or 0) / 100,
                        4,
                    ),
                    "commerce_evidence": fast_price,
                    "reason": (
                        "Live-fast verified retailer identity and "
                        "primary price evidence"
                    ),
                }

        if resolved is None and live_fast:
            # Live visitor mode is intentionally independent of Tavily /
            # official-source deep search. If retailer identity or price
            # evidence is insufficient, fail this candidate quickly and
            # transparently rather than falling back to a slow network
            # resolver.
            failures.append({
                "candidate_id": candidate_id,
                "title": raw_title,
                "stage": "live_commerce_verification",
                "status": "not_verified",
                "reason": "Live-fast commerce verification did not pass",
                "commerce_identity_score": fast_identity.get("score"),
                "commerce_identity_decision": fast_identity.get("decision"),
                "commerce_identity_reasons": fast_identity.get("reasons", []),
                "commerce_price_verified": fast_price.get("verified"),
                "commerce_price": fast_price.get("price"),
                "commerce_price_reason": fast_price.get("reason"),
            })
            continue

        if resolved is None:
            try:
                resolved = resolve_with_fallback(
                    client,
                    candidate,
                    identity,
                )
            except Exception as error:
                failures.append({
                    "candidate_id": candidate_id,
                    "title": raw_title,
                    "stage": "official_source",
                    "reason": str(error),
                })
                continue

        resolver_records.append(resolved)

        if resolved.get("verified") is not True:
            # ---------------------------------------------------------
            # VERIFIED COMMERCE-EVIDENCE FALLBACK
            # ---------------------------------------------------------
            # Official manufacturer evidence remains preferred.
            # However, absence of Tavily/general-search availability
            # must not discard a product when its discovered retailer
            # page itself provides strong product identity + verified
            # primary buy-box price evidence.
            #
            # Safety remains fail-closed:
            #   1. retailer page must pass compare_identity()
            #   2. identity decision must be "verified"
            #   3. price evidence must independently be verified
            # ---------------------------------------------------------

            market_url = clean(candidate.get("source_url"))
            market_title = clean(candidate.get("title") or raw_title)

            try:
                commerce_identity_obj = compare_identity(
                    expected_text=clean(
                        identity.get("search_name")
                        or identity.get("model")
                        or raw_title
                    ),
                    candidate_title=market_title,
                    candidate_url=market_url,
                    expected_brand=clean(identity.get("brand")),
                )
                commerce_identity = commerce_identity_obj.to_dict()
            except Exception as error:
                commerce_identity = {
                    "score": 0,
                    "decision": "reject",
                    "reasons": [
                        f"Commerce identity comparison failed: {error}"
                    ],
                }

            commerce_price = build_price_evidence(candidate)

            commerce_verified = bool(
                clean(commerce_identity.get("decision")).lower() == "verified"
                and commerce_price.get("verified") is True
                and commerce_price.get("price") is not None
            )

            if commerce_verified:
                resolved = dict(resolved)
                resolved["verified"] = True
                resolved["status"] = "commerce_evidence_verified"
                resolved["resolver_mode"] = "verified_retailer_fallback"
                resolved["official_url"] = market_url
                resolved["official_title"] = market_title
                resolved["identity_score"] = int(
                    commerce_identity.get("score") or 0
                )
                resolved["identity_decision"] = commerce_identity.get(
                    "decision"
                )
                resolved["identity_reasons"] = commerce_identity.get(
                    "reasons", []
                )
                resolved["match_score"] = round(
                    int(commerce_identity.get("score") or 0) / 100,
                    4,
                )
                resolved["commerce_evidence"] = commerce_price
            else:
                failures.append({
                    "candidate_id": candidate_id,
                    "title": raw_title,
                    "brand": identity.get("brand"),
                    "search_name": identity.get("search_name"),
                    "stage": "official_source",
                    "status": resolved.get("status"),
                    "resolver_mode": resolved.get("resolver_mode"),
                    "reason": clean(resolved.get("reason")),
                    "commerce_identity_score": commerce_identity.get(
                        "score"
                    ),
                    "commerce_identity_decision": commerce_identity.get(
                        "decision"
                    ),
                    "commerce_identity_reasons": commerce_identity.get(
                        "reasons", []
                    ),
                    "commerce_price_verified": commerce_price.get(
                        "verified"
                    ),
                    "commerce_price": commerce_price.get("price"),
                    "commerce_price_reason": commerce_price.get("reason"),
                })
                continue

        cached_extraction = find_verified_evidence(
            asin=clean(
                candidate.get("asin")
                or identity.get("asin")
            ),
            brand=clean(identity.get("brand")),
            model=clean(identity.get("model")),
            search_name=clean(identity.get("search_name")),
            title=raw_title,
        )

        if cached_extraction:
            extraction = {
                "search_name": clean(
                    cached_extraction.get("search_name")
                    or identity.get("search_name")
                    or raw_title
                ),
                "brand": clean(
                    cached_extraction.get("brand")
                    or identity.get("brand")
                ),
                "specifications": (
                    cached_extraction.get("specifications")
                    or {}
                ),
                "features": (
                    cached_extraction.get("features")
                    or []
                ),
                "review": (
                    cached_extraction.get("review")
                    or {
                        "status": "verified_cache",
                        "reason": "Verified persistent evidence cache hit",
                    }
                ),
                "fetch_status": "success",
                "resolver_verified": True,
                "page_identity_score": (
                    cached_extraction.get("page_identity_score")
                ),
                "official_url": clean(
                    cached_extraction.get("official_url")
                ),
                "evidence_mode": "verified_persistent_cache",
                "cache_match_mode": clean(
                    cached_extraction.get("cache_match_mode")
                ),
            }

        elif (
            live_fast
            and clean(resolved.get("resolver_mode"))
                == "verified_retailer_fallback"
        ):
            # -----------------------------------------------------
            # FAST LIVE EVIDENCE
            # -----------------------------------------------------
            # Commerce identity and primary retailer price were
            # already independently verified above.
            #
            # For live visitor requests, avoid a second deep page
            # crawl. Use the trusted retailer listing text as
            # bounded feature evidence. Unknown criteria remain
            # unknown; no missing specification is invented.
            # -----------------------------------------------------

            source_title = clean(
                candidate.get("source_title")
                or candidate.get("title")
                or raw_title
            )

            snippet = clean(candidate.get("snippet"))

            fast_features = [
                value
                for value in (source_title, snippet)
                if value
            ]

            extraction = {
                "fetch_status": "success",
                "resolver_verified": True,
                "page_identity_score": round(
                    int(resolved.get("identity_score") or 0) / 100,
                    4,
                ),
                "search_name": clean(
                    identity.get("search_name")
                    or candidate.get("title")
                ),
                "brand": clean(identity.get("brand")),
                "specifications": {},
                "features": fast_features,
                "review": {
                    "status": "verified_live_commerce",
                    "reason": (
                        "Fast live mode used already verified retailer "
                        "identity, listing evidence and primary price"
                    ),
                },
                "evidence_mode": "verified_commerce_fast",
            }

        else:
            try:
                extraction = extract_one(resolved, identity)
            except Exception as error:
                failures.append({
                    "candidate_id": candidate_id,
                    "title": raw_title,
                    "stage": "evidence",
                    "reason": str(error),
                })
                continue

        # Persist only genuinely verified deep extraction evidence.
        # Fast listing-only evidence is intentionally not saved as
        # long-term product knowledge.
        if clean(extraction.get("evidence_mode")) not in {
            "verified_commerce_fast",
            "verified_persistent_cache",
        }:
            try:
                save_verified_evidence(
                    identity=identity,
                    extraction=extraction,
                    asin=clean(
                        candidate.get("asin")
                        or identity.get("asin")
                    ),
                )
            except Exception:
                pass

        evidence_records.append(extraction)

        usable, reason = extraction_is_usable(extraction)

        if not usable:
            failures.append({
                "candidate_id": candidate_id,
                "title": raw_title,
                "stage": "evidence",
                "status": extraction.get("review", {}).get("status"),
                "reason": reason,
            })
            continue

        try:
            profile = runtime_profile_from_extraction(
                candidate=candidate,
                identity=identity,
                resolved=resolved,
                extraction=extraction,
                intent=intent,
            )
            # Consolidate existing verified evidence before scoring.
            # This remains network-free and never invents missing specs.
            profile = enrich_priority_evidence(
                profile=profile,
                candidate=candidate,
                extraction=extraction,
                intent=intent,
            )

            profile = retrieve_missing_priority_evidence(
                profile=profile,
                intent=intent,
            )

            # Final evidence-contract gate.
            # Regardless of which cache/enrichment path produced the
            # profile, scoring always consumes canonical list[str]
            # feature evidence.
            profile["features"] = normalize_feature_corpus(
                profile.get("features") or []
            )

            profile["fit_signals"] = build_fit_signals(profile, intent)

            assessment = calculate_product_fit(profile, intent)
        except Exception as error:
            failures.append({
                "candidate_id": candidate_id,
                "title": raw_title,
                "stage": "fit",
                "reason": str(error),
            })
            continue

        scored_records.append({
            "candidate": candidate,
            "identity": identity,
            "resolved": resolved,
            "extraction": extraction,
            "profile": profile,
            "fit_assessment": assessment,
        })

    qualifying = [
        item
        for item in scored_records
        if item.get("fit_assessment", {}).get("eligible") is True
        and int(item.get("fit_assessment", {}).get("fit_percent") or 0)
        >= MIN_FIT_PERCENT
    ]

    qualifying.sort(
        key=lambda item: (
            int(item["fit_assessment"].get("fit_percent") or 0),
            int(item["fit_assessment"].get("evidence_coverage_percent") or 0),
        ),
        reverse=True,
    )

    # ---------------------------------------------------------
    # MODEL-LEVEL RECOMMENDATION DEDUPLICATION
    # ---------------------------------------------------------
    # Multiple retailer ASINs / colours / listings may represent
    # the same underlying phone model. Keep only the strongest
    # already-ranked listing for each model family.
    #
    # This affects presentation/ranking only. It does not change
    # product evidence, fit scoring or eligibility.
    # ---------------------------------------------------------

    def recommendation_model_key(item: dict[str, Any]) -> str:
        profile = item.get("profile", {}) or {}

        title = clean(profile.get("title")).lower()
        brand = clean(profile.get("brand")).lower()

        # Remove common commerce variant descriptors which should
        # not make the same model appear as a separate recommendation.
        cleaned = re.sub(
            r"\([^)]*\)",
            " ",
            title,
        )

        cleaned = re.sub(
            r"\b(?:"
            r"\d+\s*gb(?:\s+ram|\s+storage|\s+rom)?|"
            r"\d+gb|"
            r"ram|rom|storage|"
            r"pantone|"
            r"black|blue|green|grey|gray|silver|purple|"
            r"yellow|white|red|cyan|frost|pearl|metallic|"
            r"brilliant|nautical|capri|radiant|arctic"
            r")\b",
            " ",
            cleaned,
            flags=re.I,
        )

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Manufacturer shorthand must not create duplicate model keys.
        # Motorola commonly appears as both:
        #   Motorola Moto g37 Power
        #   Motorola g37 Power
        if brand == "motorola":
            cleaned = re.sub(
                r"^(?:motorola\s+)?moto\s+",
                "",
                cleaned,
                flags=re.I,
            )
            cleaned = re.sub(
                r"^motorola\s+",
                "",
                cleaned,
                flags=re.I,
            )

        # Brand is already carried separately in the key.
        if brand and cleaned.startswith(brand + " "):
            cleaned = cleaned[len(brand):].strip()

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return f"{brand}|{cleaned}".strip("|")

    deduped_qualifying: list[dict[str, Any]] = []
    seen_model_keys: set[str] = set()

    for item in qualifying:
        key = recommendation_model_key(item)

        if not key:
            key = clean(
                item.get("profile", {}).get("product_id")
            ).lower()

        if key in seen_model_keys:
            continue

        seen_model_keys.add(key)
        deduped_qualifying.append(item)

    qualifying = deduped_qualifying

    recommendations: list[dict[str, Any]] = []

    for rank, item in enumerate(qualifying[:max_results], start=1):
        assessment = item["fit_assessment"]
        profile = item["profile"]
        strong, tradeoffs, unknown = criterion_groups(assessment)

        recommendations.append({
            "rank": rank,
            "product_id": profile.get("product_id"),
            "title": profile.get("title"),
            "brand": profile.get("brand"),
            "price": profile.get("price"),
            "asin": profile.get("asin"),
            "image_url": profile.get("image_url"),
            "commerce_provider": profile.get("commerce_provider"),
            "fit_percent": assessment.get("fit_percent"),
            "raw_fit_percent": assessment.get("raw_fit_percent"),
            "evidence_coverage_percent": assessment.get(
                "evidence_coverage_percent"
            ),
            "confidence": assessment.get("recommendation_confidence"),
            "why_it_fits": strong[:5],
            "tradeoffs": tradeoffs[:4],
            "unknown": unknown[:4],
            "official_source": profile.get("official_product_url"),
            "market_source": profile.get("market_source_url"),
            "provenance": profile.get("provenance", {}),
        })

    failure_counter = Counter()

    for failure in failures:
        key = (
            clean(failure.get("stage")),
            clean(failure.get("status")) or clean(failure.get("reason")),
        )
        failure_counter[key] += 1

    failure_summary = [
        {
            "stage": stage,
            "reason_or_status": reason,
            "count": count,
        }
        for (stage, reason), count in failure_counter.most_common()
    ]

    status = "PASS" if len(recommendations) >= DEFAULT_MIN_RESULTS else "PARTIAL"

    fit_diagnostics = []

    for item in scored_records:
        assessment = item.get("fit_assessment", {})
        profile = item.get("profile", {})

        fit_diagnostics.append({
            "product_id": profile.get("product_id"),
            "title": profile.get("title"),
            "brand": profile.get("brand"),
            "price": profile.get("price"),
            "eligible": assessment.get("eligible"),
            "fit_percent": assessment.get("fit_percent"),
            "raw_fit_percent": assessment.get("raw_fit_percent"),
            "evidence_coverage_percent": assessment.get(
                "evidence_coverage_percent"
            ),
            "confidence": assessment.get("recommendation_confidence"),
            "hard_constraint_failures": assessment.get(
                "hard_constraint_failures", []
            ),
            "criteria": assessment.get("criteria", []),
            "attributes": profile.get("attributes", {}),
            "features": profile.get("features", []),
            "price_evidence": profile.get(
                "provenance", {}
            ).get("price_evidence", {}),
            "official_source": profile.get("official_product_url"),
            "market_source": profile.get("market_source_url"),
            "resolver_mode": profile.get("provenance", {}).get("resolver_mode"),
            "resolver_status": profile.get("provenance", {}).get("resolver_status"),
            "resolver_identity_score": profile.get("provenance", {}).get("resolver_identity_score"),
            "resolver_match_score": profile.get("provenance", {}).get("resolver_match_score"),
            "extractor_page_identity_score": profile.get("provenance", {}).get("extractor_page_identity_score"),
            "extractor_review_status": profile.get("provenance", {}).get("extractor_review_status"),
        })

    total_seconds = time.perf_counter() - pipeline_started

    return {
        "timings": {
            "intent_seconds": round(intent_seconds, 3),
            "discovery_seconds": round(discovery_seconds, 3),
            "total_seconds": round(total_seconds, 3),
        },
        "schema_version": "1.1",
        "query": query,
        "intent": intent,
        "stage_counts": {
            "discovered": len(discovered),
            "identity_prepared": len(identities),
            "official_verified": sum(
                1 for x in resolver_records if x.get("verified") is True
            ),
            "evidence_ready": sum(
                1 for x in evidence_records if extraction_is_usable(x)[0]
            ),
            "fit_scored": len(scored_records),
            "qualifying_50_plus": len(qualifying),
            "recommendations_returned": len(recommendations),
        },
        "recommendations": recommendations,
        "fit_diagnostics": fit_diagnostics,
        "failure_summary": failure_summary,
        "failures": failures,
        "status": status,
        "rules": {
            "min_fit_percent": MIN_FIT_PERCENT,
            "preferred_minimum_results": DEFAULT_MIN_RESULTS,
            "maximum_results": max_results,
            "affiliate_affects_fit": False,
            "discovery_score_affects_fit": False,
            "auto_publish": False,
            "unknown_evidence_is_zero": False,
        },
    }


def save_runtime_payload(payload: dict[str, Any]) -> None:
    RUNTIME_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def print_result(payload: dict[str, Any]) -> None:
    c = payload["stage_counts"]

    print("=" * 78)
    print("COUPON WORLD SHOPPING INTELLIGENCE PIPELINE v1.1")
    print("=" * 78)
    print("QUERY:", payload["query"])
    print()
    print("DISCOVERED         :", c["discovered"])
    print("IDENTITY PREPARED  :", c["identity_prepared"])
    print("OFFICIAL VERIFIED  :", c["official_verified"])
    print("EVIDENCE READY     :", c["evidence_ready"])
    print("FIT SCORED         :", c["fit_scored"])
    print("QUALIFYING >=50%   :", c["qualifying_50_plus"])
    print("RECOMMENDATIONS    :", c["recommendations_returned"])
    print()

    for rec in payload["recommendations"]:
        print("-" * 78)
        print(f'#{rec["rank"]} | {rec["title"]}')
        print("BRAND:", rec["brand"])
        print("FIT:", f'{rec["fit_percent"]}%')
        print("RAW FIT:", f'{rec["raw_fit_percent"]}%')
        print(
            "EVIDENCE COVERAGE:",
            f'{rec["evidence_coverage_percent"]}%',
        )
        print("CONFIDENCE:", clean(rec["confidence"]).upper())

        if rec["why_it_fits"]:
            print("WHY IT FITS:")
            for item in rec["why_it_fits"]:
                print("  +", item)

        if rec["tradeoffs"]:
            print("TRADE-OFFS:")
            for item in rec["tradeoffs"]:
                print("  -", item)

        if rec["unknown"]:
            print("UNKNOWN:")
            for item in rec["unknown"]:
                print("  ?", item)

        print("OFFICIAL SOURCE:", rec["official_source"])
        print("MARKET SOURCE  :", rec["market_source"])

    print()
    print("FAILURE SUMMARY:")

    if not payload["failure_summary"]:
        print("  None")
    else:
        for item in payload["failure_summary"][:10]:
            print(
                f'  {item["count"]}x | '
                f'{item["stage"]} | '
                f'{item["reason_or_status"]}'
            )

    print()
    print("STATUS:", payload["status"])

    if payload["status"] == "PARTIAL":
        print(
            "No weak, unverified, or <50% product was added "
            "just to fill Top 3-5."
        )

    print("RUNTIME OUTPUT:", RUNTIME_OUTPUT)
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coupon World end-to-end shopping intelligence pipeline"
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--max-candidates", type=int, default=15)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        payload = run_pipeline(
            query=args.query,
            max_candidates=max(3, min(int(args.max_candidates), 30)),
            max_results=max(1, min(int(args.max_results), DEFAULT_MAX_RESULTS)),
        )
    except Exception as error:
        print("PIPELINE ERROR:", str(error))
        return 1

    save_runtime_payload(payload)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_result(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
