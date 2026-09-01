#!/usr/bin/env python3
"""
Coupon World AI OS
Market Discovery Engine v1.6.1

Two-channel discovery:
1) Commerce discovery: search known retailer domains for actual product pages.
2) Open-web discovery: search broadly, but accept only strong product-detail URLs.

Important:
- Discovery only creates an UNVERIFIED candidate pool.
- Search relevance is never treated as final recommendation Fit.
- Affiliate status does not affect candidate ranking.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient
from amazon_search_image_resolver import search_asins

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

DISCOVERY_CACHE_PATH = ROOT / "data" / "market_discovery_cache.json"
DISCOVERY_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from intent_engine import parse_query
from official_source_resolver import (
    BRAND_DOMAINS,
    duckduckgo_official_search,
)


COMMERCE_DOMAINS = [
    "amazon.in",
    "flipkart.com",
    "croma.com",
    "reliancedigital.in",
    "vijaysales.com",
]

EXCLUDED_HOSTS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "x.com", "twitter.com", "www.twitter.com",
    "reddit.com", "www.reddit.com",
    "pinterest.com", "www.pinterest.com",
}

NON_PRODUCT_PATH_FRAGMENTS = (
    "/news/", "/blog/", "/blogs/", "/article/", "/articles/",
    "/review/", "/reviews/", "/compare/", "/comparison/",
    "/forum/", "/community/", "/support/", "/guide/", "/guides/",
    "/best-", "/top-", "/buying-guide", "/how-to/",
    "/category/", "/categories/", "/collections/", "/collection/",
    "/price-below_", "/price-above_", "/price-range",
)

EDITORIAL_PATTERNS = (
    r"^\s*best\b",
    r"^\s*top\s+\d*\b",
    r"\bguide\b",
    r"\breview\b",
    r"\bcomparison\b",
    r"\broundup\b",
    r"\bprice list\b",
    r"\bearbuds under\b",
    r"\bphones under\b",
    r"\blaptops under\b",
)

CATEGORY_HINTS = {
    "smartphone": ("phone", "mobile", "smartphone"),
    "earbuds": ("earbuds", "earbud", "buds", "tws"),
    "headphones": ("headphone", "headphones", "headset"),
    "laptop": ("laptop", "notebook"),
    "smartwatch": ("smartwatch", "smart watch", "watch"),
    "tablet": ("tablet", "tab"),
    "speaker": ("speaker", "bluetooth speaker"),
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value: str) -> str:
    text = clean(value).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def path_of(url: str) -> str:
    try:
        return (urlparse(url).path or "").lower()
    except ValueError:
        return ""


def is_editorial_title(title: str) -> bool:
    text = clean(title).lower()
    return any(re.search(pattern, text, re.I) for pattern in EDITORIAL_PATTERNS)


def has_category_hint(title: str, category: str | None) -> bool:
    if not category:
        return True

    hints = CATEGORY_HINTS.get(category, ())
    title_l = clean(title).lower()

    return not hints or any(hint in title_l for hint in hints)


def strong_product_url(url: str) -> bool:
    host = host_of(url)
    path = path_of(url)

    if not host or not path or path == "/":
        return False

    lowered = clean(url).lower()

    if any(fragment in lowered for fragment in NON_PRODUCT_PATH_FRAGMENTS):
        return False

    if "amazon.in" in host:
        return "/dp/" in path or "/gp/product/" in path

    if "flipkart.com" in host:
        return "/p/" in path

    if "croma.com" in host:
        return "/p/" in path or "/product/" in path

    if "reliancedigital.in" in host:
        return "/product/" in path or len(path.strip("/").split("/")) >= 2

    if "vijaysales.com" in host:
        return "/p/" in path or "/product/" in path or len(path.strip("/").split("/")) >= 2

    # Open-web/manufacturer fallback:
    markers = (
        "/product/",
        "/products/",
        "/earbuds/",
        "/headphones/",
        "/smartphones/",
        "/mobile/",
        "/phone/",
        "/laptop/",
        "/laptops/",
    )

    return any(marker in path for marker in markers)


def is_search_or_listing_url(url: str) -> bool:
    """
    Reject search, category, editorial and listing URLs.

    Discovery should admit individual product-detail pages only.
    """
    url = clean(url)

    if not url:
        return True

    try:
        parsed = urlparse(url)
    except Exception:
        return True

    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower().rstrip("/")
    lowered = url.lower()

    search_markers = (
        "/search?",
        "/search/",
        "/s?",
        "?k=",
        "&k=",
        "?q=",
        "&q=",
        "search?q=",
    )

    if any(marker in lowered for marker in search_markers):
        return True

    listing_fragments = (
        "/category/",
        "/categories/",
        "/collection/",
        "/collections/",
        "/catalog/",
        "/browse/",
        "/bestsellers/",
    )

    if any(fragment in path for fragment in listing_fragments):
        return True

    editorial_fragments = (
        "/blog/",
        "/blogs/",
        "/article/",
        "/articles/",
        "/guide/",
        "/guides/",
        "/review/",
        "/reviews/",
        "/resource-center/",
        "/news/",
        "/comparison/",
        "/compare/",
    )

    if any(fragment in path for fragment in editorial_fragments):
        return True

    # Amazon search/browse pages.
    if "amazon." in host:
        if (
            path == "/s"
            or path.startswith("/s/")
            or path.startswith("/gp/bestsellers")
            or path.startswith("/b/")
        ):
            return True

    # Best Buy category/listing identifiers.
    if "bestbuy.com" in host:
        if (
            "pcmcat" in path
            or "pcmcat" in lowered
            or "/site/headphones/" in path
        ):
            return True

    return False


def looks_like_product_result(
    title: str,
    url: str,
    category: str | None,
) -> bool:
    host = host_of(url)

    if not host or host in EXCLUDED_HOSTS:
        return False

    if not clean(title) or is_editorial_title(title):
        return False

    # Never admit search/category/listing pages as product candidates.
    if is_search_or_listing_url(url):
        return False

    if not strong_product_url(url):
        return False

    # Retail product titles can omit category words, so category is a soft gate.
    if has_category_hint(title, category):
        return True

    # Still allow a strong commerce product URL even when a compact title
    # does not contain the category term.
    return any(domain in host for domain in COMMERCE_DOMAINS)


def build_discovery_queries(
    user_query: str,
    intent: dict[str, Any],
) -> list[str]:
    category = clean(intent.get("category")).replace("_", " ")
    budget = intent.get("budget_max")

    brands = [
        clean(x)
        for x in intent.get("brands", [])
        if clean(x)
    ]

    brand_terms = brands[:1]

    features = [
        clean(x)
        for x in intent.get("features", [])
        if clean(x)
    ]

    preferred = [
        clean(x).replace("_", " ")
        for x in intent.get("preferred", [])
        if clean(x)
    ]

    use_cases = [
        clean(x).replace("_", " ")
        for x in intent.get("use_case", [])
        if clean(x)
    ]

    must_have = [
        clean(x).replace("_", " ")
        for x in intent.get("must_have", [])
        if clean(x)
    ]

    tv_requirements = intent.get("tv_requirements", {})
    if not isinstance(tv_requirements, dict):
        tv_requirements = {}

    def join_unique(parts: list[object]) -> str:
        seen: set[str] = set()
        output: list[str] = []

        for value in parts:
            part = clean(value)
            key = part.lower()

            if not part or key in seen:
                continue

            seen.add(key)
            output.append(part)

        return " ".join(output)

    budget_terms: list[object] = []
    if budget not in (None, ""):
        budget_terms = ["under", str(budget)]

    queries: list[str] = []

    # --------------------------------------------------------
    # TV specialist lane: preserve explicit screen/panel requirements.
    # --------------------------------------------------------
    if category == "television" and tv_requirements:
        tv_terms = []

        screen_size = tv_requirements.get("screen_size_inches")
        if screen_size:
            tv_terms.append(f"{int(screen_size)} inch")

        panel = clean(tv_requirements.get("panel_technology"))
        panel_labels = {
            "oled": "OLED",
            "qled": "QLED",
            "mini_led": "Mini LED",
            "led": "LED",
        }

        if panel:
            tv_terms.append(panel_labels.get(panel, panel))

        refresh = tv_requirements.get("refresh_rate_hz")
        if refresh:
            tv_terms.append(f"{int(refresh)}Hz")

        if tv_requirements.get("hdmi_2_1") is True:
            tv_terms.append("HDMI 2.1")

        if tv_requirements.get("vrr") is True:
            tv_terms.append("VRR")

        if tv_requirements.get("allm") is True:
            tv_terms.append("ALLM")

        queries.append(
            join_unique(
                [
                    category,
                    *tv_terms,
                    *budget_terms,
                    "India",
                    "buy",
                ]
            )
        )

    # --------------------------------------------------------
    # Lane 0: use-case-aware discovery.
    # Preserve what the shopper intends to DO with the product.
    # --------------------------------------------------------
    if use_cases:
        use_case_terms = list(use_cases)

        if category == "laptop" and "gaming" in {
            x.lower() for x in use_cases
        }:
            use_case_terms.extend([
                "dedicated graphics",
                "RTX",
            ])

        queries.append(
            join_unique(
                [
                    category or "product",
                    *use_case_terms[:3],
                    *must_have[:2],
                    *budget_terms,
                    "India",
                    "buy",
                ]
            )
        )

    # --------------------------------------------------------
    # Lane 1: explicit must-have search.
    # --------------------------------------------------------
    if must_have:
        queries.append(
            join_unique(
                [
                    category or "product",
                    *must_have,
                    *budget_terms,
                    "India",
                    "buy",
                ]
            )
        )

    # --------------------------------------------------------
    # Lane 2: semantic expansion for important must-haves.
    # ANC is expanded because retailers may write the full phrase
    # rather than the acronym.
    # --------------------------------------------------------
    if "anc" in {x.lower() for x in must_have}:
        queries.append(
            join_unique(
                [
                    category or "product",
                    "active noise cancellation",
                    *budget_terms,
                    "India",
                    "model",
                ]
            )
        )

    # --------------------------------------------------------
    # Lane 3: must-have + user's strongest preferences.
    # --------------------------------------------------------
    queries.append(
        join_unique(
            [
                category or "product",
                *must_have[:2],
                *preferred[:2],
                *budget_terms,
                "India",
            ]
        )
    )

    # --------------------------------------------------------
    # Lane 4: feature-rich commerce query.
    # --------------------------------------------------------
    queries.append(
        join_unique(
            [
                category or "product",
                *features[:3],
                *preferred[:2],
                *budget_terms,
                "India",
                "buy",
            ]
        )
    )

    # --------------------------------------------------------
    # Mobile specialist lane: RAM / storage variant discovery.
    #
    # Commerce sources express the same phone capacity in several ways:
    #   8GB RAM 256GB
    #   8GB + 256GB
    #   8+256GB
    #   (8 GB RAM, 256 GB)
    #
    # Discovery should maximize recall across these representations.
    # Exact capacity compliance remains the responsibility of the
    # downstream evidence / hard-constraint verification layer.
    # --------------------------------------------------------
    if category in {"mobile", "phone", "smartphone", "mobile phone"}:
        query_text = " ".join(
            [
                clean(user_query),
                *must_have,
                *features,
            ]
        )

        ram_match = re.search(
            r"\b(\d{1,3})\s*gb(?:\s*ram|_ram)?\b",
            query_text,
            re.I,
        )

        storage_match = re.search(
            r"\b(\d{2,4})\s*gb(?:\s*(?:storage|rom|internal storage)|_storage)?\b",
            query_text,
            re.I,
        )

        ram_gb = int(ram_match.group(1)) if ram_match else None
        storage_gb = int(storage_match.group(1)) if storage_match else None

        # Avoid accidentally treating the RAM number as storage when
        # both capacities are written in normal shopper wording.
        if ram_gb is not None:
            storage_candidates = [
                int(value)
                for value in re.findall(
                    r"\b(\d{2,4})\s*gb\b",
                    query_text,
                    re.I,
                )
                if int(value) != ram_gb
            ]

            if storage_candidates:
                storage_gb = max(storage_candidates)

        if ram_gb is not None and storage_gb is not None:
            # Retailer-style identity query.
            #
            # Keep this deliberately clean: budget / India / "buy" terms
            # can reduce exact-variant recall on retailer search pages.
            # Budget compliance is enforced downstream from verified price.
            if brand_terms:
                brand = brand_terms[0]

                brand_family = {
                    "samsung": "Galaxy",
                }.get(normalize_key(brand))

                queries.append(
                    join_unique(
                        [
                            brand,
                            brand_family,
                            f"{storage_gb}GB",
                            f"{ram_gb}GB RAM",
                        ]
                    )
                )

            capacity_variants = [
                f"{ram_gb}GB RAM {storage_gb}GB",
                f"{ram_gb}GB {storage_gb}GB",
                f"{ram_gb}GB+{storage_gb}GB",
            ]

            for capacity_variant in capacity_variants:
                queries.append(
                    join_unique(
                        [
                            *brand_terms,
                            category or "smartphone",
                            capacity_variant,
                            *budget_terms,
                            "India",
                            "buy",
                        ]
                    )
                )

    # Preserve an explicit shopper brand across generated lanes.
    # The original-user-query lane already contains the user's wording.
    if brand_terms:
        brand = brand_terms[0]
        branded_queries: list[str] = []

        for generated_query in queries:
            if brand.lower() in generated_query.lower():
                branded_queries.append(generated_query)
            else:
                branded_queries.append(
                    join_unique([brand, generated_query])
                )

        queries = branded_queries

    # --------------------------------------------------------
    # Lane 5: original user wording.
    # This helps preserve nuance not represented in structured intent.
    # --------------------------------------------------------
    queries.append(
        join_unique(
            [
                clean(user_query),
                "India",
                "product",
            ]
        )
    )

    # --------------------------------------------------------
    # Lane 6: broad model fallback.
    # --------------------------------------------------------
    queries.append(
        join_unique(
            [
                *brand_terms,
                category or "product",
                *must_have[:1],
                *budget_terms,
                "India",
                "model",
            ]
        )
    )

    seen: set[str] = set()
    unique: list[str] = []

    for query in queries:
        normalized = clean(query)
        key = normalized.lower()

        if normalized and key not in seen:
            seen.add(key)
            unique.append(normalized)

    return unique


def compact_product_title(title: str) -> str:
    title = clean(title)

    # Remove common retailer/search-engine SEO tails.
    title = re.sub(
        r"\s+Price in India\s*-\s*Buy\s+.*$",
        "",
        title,
        flags=re.I,
    )

    title = re.sub(
        r"\s*-\s*(?:Amazon|Flipkart|Croma|Reliance Digital|Vijay Sales).*$",
        "",
        title,
        flags=re.I,
    )

    title = re.sub(
        r"\s*:\s*(?:Amazon\.in|Flipkart\.com|Croma\.com)\s*$",
        "",
        title,
        flags=re.I,
    )

    # Common page-title separators.
    for separator in (" | ", " ? ", " ? ", " || "):
        if separator in title:
            left = clean(title.split(separator, 1)[0])
            if len(left.split()) >= 2:
                title = left
                break

    return clean(title)



def discovery_cache_key(query: str, category: str | None) -> str:
    return f"{normalize_key(category or '')}::{normalize_key(query)}"


def load_discovery_cache() -> dict[str, Any]:
    if not DISCOVERY_CACHE_PATH.exists():
        return {}

    try:
        payload = json.loads(
            DISCOVERY_CACHE_PATH.read_text(encoding="utf-8-sig")
        )
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}


def save_discovery_cache(cache: dict[str, Any]) -> None:
    DISCOVERY_CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = DISCOVERY_CACHE_PATH.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp.replace(DISCOVERY_CACHE_PATH)


def cache_discovery_results(
    *,
    query: str,
    category: str | None,
    results: list[dict[str, Any]],
) -> None:
    if not results:
        return

    safe_results = []

    for item in results:
        if not isinstance(item, dict):
            continue

        title = clean(item.get("title"))
        url = clean(item.get("url"))

        if not title or not url:
            continue

        safe_results.append(
            {
                "title": title,
                "url": url,
                "host": clean(item.get("host")) or host_of(url),
                "content": clean(item.get("content")),
                "search_score": float(item.get("search_score") or 0),
                "query": clean(item.get("query")) or query,
                "channel": clean(item.get("channel")) or "commerce",
                "provider": clean(item.get("provider")) or "cached_provider",
                "asin": clean(item.get("asin")),
                "search_image": clean(item.get("search_image")),
                "search_price_text": clean(item.get("search_price_text")),
                "search_price_currency": clean(
                    item.get("search_price_currency")
                ),
                "search_price_evidence_method": clean(
                    item.get("search_price_evidence_method")
                ),
            }
        )

    if not safe_results:
        return

    cache = load_discovery_cache()
    key = discovery_cache_key(query, category)

    cache[key] = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "category": category,
        "results": safe_results,
    }

    try:
        save_discovery_cache(cache)
    except OSError:
        pass


def get_recent_discovery_cache(
    *,
    query: str,
    category: str | None,
    max_results: int,
) -> list[dict[str, Any]]:
    cache = load_discovery_cache()
    key = discovery_cache_key(query, category)
    record = cache.get(key)

    if not isinstance(record, dict):
        return []

    saved_at = clean(record.get("saved_at"))

    if not saved_at:
        return []

    try:
        timestamp = datetime.fromisoformat(
            saved_at.replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        age_seconds = (
            datetime.now(timezone.utc) - timestamp
        ).total_seconds()
    except Exception:
        return []

    if (
        age_seconds < 0
        or age_seconds > DISCOVERY_CACHE_MAX_AGE_SECONDS
    ):
        return []

    raw_results = record.get("results", [])

    if not isinstance(raw_results, list):
        return []

    results: list[dict[str, Any]] = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        restored = dict(item)
        restored["provider"] = (
            "recent_discovery_cache:"
            + clean(item.get("provider"))
        )
        restored["cache_age_seconds"] = round(age_seconds)

        results.append(restored)

        if len(results) >= max_results:
            break

    return results

def local_known_product_fallback(
    *,
    query: str,
    category: str | None,
    max_results: int,
) -> list[dict[str, Any]]:
    """
    Search Coupon World's accumulated local product knowledge when live
    discovery providers are unavailable.

    This is a resilience fallback only:
    - candidates remain unverified;
    - no local ranking becomes final recommendation Fit;
    - retailer/official evidence must still pass downstream gates.
    """

    query_key = normalize_key(query)
    query_tokens = {
        token
        for token in query_key.split()
        if len(token) >= 2
    }

    if not query_tokens:
        return []

    candidates: list[dict[str, Any]] = []

    def add_candidate(
        *,
        title: str,
        url: str,
        brand: str = "",
        source: str,
        extra_score: float = 0.0,
    ) -> None:
        title = clean(title)
        url = clean(url)

        if not title or not url:
            return

        if not looks_like_product_result(title, url, category):
            return

        title_tokens = set(normalize_key(title).split())
        brand_tokens = set(normalize_key(brand).split())

        overlap = len(query_tokens & title_tokens)

        if overlap == 0:
            return

        score = overlap / max(1, len(query_tokens))

        if brand_tokens and query_tokens & brand_tokens:
            score += 0.20

        score += extra_score

        candidates.append(
            {
                "title": title,
                "url": url,
                "host": host_of(url),
                "content": "",
                "search_score": round(min(score, 1.0), 4),
                "query": query,
                "channel": "commerce",
                "provider": source,
            }
        )

    # ---------------------------------------------------------
    # Source 1: accumulated official research results.
    # ---------------------------------------------------------
    research_path = ROOT / "data" / "research_results.json"

    try:
        research = json.loads(
            research_path.read_text(encoding="utf-8-sig")
        )
    except Exception:
        research = {}

    research_products = (
        research.get("products", [])
        if isinstance(research, dict)
        else []
    )

    for product in research_products:
        if not isinstance(product, dict):
            continue

        add_candidate(
            title=clean(product.get("title")),
            url=clean(product.get("official_url")),
            brand=clean(product.get("brand")),
            source="local_research_cache",
            extra_score=0.08 if product.get("verified") is True else 0.0,
        )

    # ---------------------------------------------------------
    # Source 2: current Coupon World commerce catalogue.
    # ---------------------------------------------------------
    catalogue_path = ROOT / "coupons.json"

    try:
        catalogue = json.loads(
            catalogue_path.read_text(encoding="utf-8-sig")
        )
    except Exception:
        catalogue = []

    catalogue_products = (
        catalogue
        if isinstance(catalogue, list)
        else catalogue.get("products", [])
        if isinstance(catalogue, dict)
        else []
    )

    for product in catalogue_products:
        if not isinstance(product, dict):
            continue

        if product.get("active") is False:
            continue

        add_candidate(
            title=clean(product.get("title")),
            url=clean(product.get("link")),
            brand=clean(product.get("brand")),
            source="local_coupon_catalogue",
            extra_score=0.05,
        )

    # Deduplicate and rank locally.
    best_by_url: dict[str, dict[str, Any]] = {}

    for item in candidates:
        url = clean(item.get("url"))

        if not url:
            continue

        previous = best_by_url.get(url)

        if (
            previous is None
            or float(item.get("search_score") or 0)
            > float(previous.get("search_score") or 0)
        ):
            best_by_url[url] = item

    ranked = list(best_by_url.values())

    ranked.sort(
        key=lambda item: float(item.get("search_score") or 0),
        reverse=True,
    )

    return ranked[:max_results]

def fallback_search_channel(
    *,
    query: str,
    category: str | None,
    include_domains: list[str] | None,
    channel: str,
    max_results: int,
) -> list[dict[str, Any]]:
    """
    Runtime discovery fallback using the existing Amazon search-card
    infrastructure.

    This is discovery only. Search position, Amazon relevance and
    merchant presence do not affect final Fit.

    All candidates remain unverified and must pass the existing
    downstream identity/evidence gates.
    """

    # Amazon fallback is currently a commerce discovery lane.
    # Open-web fallback must not pretend Amazon is independent
    # corroborating evidence.
    if channel != "commerce":
        return []

    # First collect Coupon World's accumulated local knowledge.
    # Do not return early: local knowledge may be incomplete or may
    # contain candidates that downstream category gates later reject.
    local_results = local_known_product_fallback(
        query=query,
        category=category,
        max_results=max_results,
    )

    # Amazon remains an optional independent discovery lane.
    try:
        raw_results = search_asins(
            query,
            max_cards=max(3, min(max_results, 20)),
        )
    except Exception:
        raw_results = []

    accepted: list[dict[str, Any]] = list(local_results)

    for result in raw_results:
        if not isinstance(result, dict):
            continue

        title = clean(result.get("search_title"))
        url = clean(result.get("product_url"))

        if not title or not url:
            continue

        if not looks_like_product_result(
            title,
            url,
            category,
        ):
            continue

        accepted.append(
            {
                "title": title,
                "url": url,
                "host": host_of(url),
                "content": "",
                "search_score": 0.5,
                "query": query,
                "channel": channel,
                "provider": "amazon_search_cards",
                "asin": clean(result.get("asin")),
                "search_image": clean(
                    result.get("search_image")
                ),
                "search_price_text": clean(
                    result.get("search_price_text")
                ),
                "search_price_currency": clean(
                    result.get("search_price_currency")
                ),
                "search_price_evidence_method": clean(
                    result.get("search_price_evidence_method")
                ),
            }
        )

        # Do not stop live Amazon collection because local fallback
        # candidates already consumed part of max_results.
        #
        # search_asins() already limits the Amazon card count.
        # Downstream purity / variant / brand gates should decide which
        # candidates survive.
        #
        # This is important for constrained searches such as
        # "Samsung 8GB RAM 256GB under 25000", where the correct variant
        # may appear later in Amazon's search results.

    live_amazon_results = [
        item
        for item in accepted
        if clean(item.get("provider")) == "amazon_search_cards"
    ]

    if live_amazon_results:
        cache_discovery_results(
            query=query,
            category=category,
            results=live_amazon_results,
        )
    else:
        cached_results = get_recent_discovery_cache(
            query=query,
            category=category,
            max_results=max_results,
        )

        seen_urls = {
            clean(item.get("url"))
            for item in accepted
            if clean(item.get("url"))
        }

        for item in cached_results:
            url = clean(item.get("url"))

            if not url or url in seen_urls:
                continue

            accepted.append(item)
            seen_urls.add(url)

            if len(accepted) >= max_results:
                break

    return accepted

def search_channel(
    client: TavilyClient,
    *,
    query: str,
    category: str | None,
    include_domains: list[str] | None,
    channel: str,
    max_results: int,
) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
    }

    if include_domains:
        kwargs["include_domains"] = include_domains

    response = client.search(**kwargs)

    accepted: list[dict[str, Any]] = []

    for result in response.get("results", []):
        if not isinstance(result, dict):
            continue

        title = clean(result.get("title"))
        url = clean(result.get("url"))

        if not looks_like_product_result(title, url, category):
            continue

        accepted.append(
            {
                "title": title,
                "url": url,
                "host": host_of(url),
                "content": clean(result.get("content")),
                "search_score": float(result.get("score") or 0),
                "query": query,
                "channel": channel,
            }
        )

    return accepted


def known_brand_from_title(title: str) -> str | None:
    normalized = normalize_key(title)

    if not normalized:
        return None

    # Retail/platform words must never become product brands.
    non_product_brands = {
        "amazon",
        "echo",
    }

    # Some valid brand names are also common feature words.
    # They require stronger positional evidence.
    ambiguous_brands = {
        "noise",
    }

    for brand in sorted(BRAND_DOMAINS.keys(), key=len, reverse=True):
        if brand in non_product_brands:
            continue

        brand_tokens = normalize_key(brand)

        if not brand_tokens:
            continue

        pattern = rf"(?:^|\s){re.escape(brand_tokens)}(?:\s|$)"

        if not re.search(pattern, normalized):
            continue

        if brand in ambiguous_brands:
            # "Noise" should count as the Noise brand only when it appears
            # as product identity near the beginning of the title.
            first_tokens = normalized.split()[:4]

            if brand_tokens not in first_tokens:
                continue

        return brand

    return None


def is_generic_listing_title(title: str) -> bool:
    text = normalize_key(title)

    if not text:
        return True

    generic_patterns = (
        r"^buy truly wireless earbuds online",
        r"^buy wireless earbuds online",
        r"^truly wireless earbuds online",
        r"^wireless earbuds online",
        r"^earbuds online at best price",
        r"^best price earbuds",
        r"^shop earbuds online",
        r"^buy earbuds online",
    )

    if any(re.search(pattern, text, re.I) for pattern in generic_patterns):
        return True

    # Titles with no meaningful product/model identity.
    generic_only = {
        "earbuds",
        "wireless earbuds",
        "bluetooth earbuds",
        "tws earbuds",
        "true wireless earbuds",
        "truly wireless earbuds",
    }

    return text in generic_only


def model_identity_signal(title: str) -> float:
    text = clean(title)

    if not text:
        return 0.0

    score = 0.0

    # Model identities commonly contain numbers:
    # N1, Buds 3 Pro, A466, 510BT, etc.
    if re.search(r"\b[a-z]*\d+[a-z0-9-]*\b", text, re.I):
        score += 0.12

    # Product-family/model modifiers are useful identity evidence.
    if re.search(
        r"\b(pro|plus|ultra|lite|neo|core|air|nord|buds|ear|tune)\b",
        text,
        re.I,
    ):
        score += 0.06

    return min(score, 0.18)


def candidate_quality_score(item: dict[str, Any], title: str) -> float:
    """
    Discovery quality only.

    This is NOT final product Fit and must never be presented
    as a recommendation score.
    """
    score = float(item.get("search_score") or 0)

    brand = known_brand_from_title(title)

    if brand:
        score += 0.22

    score += model_identity_signal(title)

    # Unknown brands remain eligible; they simply receive no
    # known-brand confidence boost and must prove themselves downstream.

    return round(score, 4)


def _capacity_values_from_title(
    title: str,
    kind: str,
) -> list[int]:
    """
    Extract explicitly stated physical RAM/storage capacities.

    Conservative by design:
    - returns [] when evidence is absent/ambiguous;
    - does not infer capacities;
    - does not count extended/virtual RAM as physical RAM.
    """
    text = clean(title).lower()
    values: list[int] = []

    if kind == "ram":
        patterns = [
            r"\b(\d{1,3})\s*gb\s*(?:physical\s*)?ram\b",
            r"\b(\d{1,3})\s*gb\s*\+\s*\d{1,3}\s*gb\s*(?:virtual|dynamic|extended)\s*ram\b",
            r"\b(\d{1,3})\s*gb\s*\+\s*\d{1,3}\s*gb\s*ram\b",
            r"\b(\d{1,3})\s*\+\s*\d{1,3}\s*\*?\s*gb\s*ram\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.I):
                value = int(match.group(1))
                if value not in values:
                    values.append(value)

        # Common commerce shorthand: 8GB+128GB.
        for match in re.finditer(
            r"\b(\d{1,3})\s*gb\s*\+\s*(\d{2,4})\s*gb\b",
            text,
            flags=re.I,
        ):
            ram = int(match.group(1))
            storage = int(match.group(2))

            if ram <= 64 and storage >= 32 and ram not in values:
                values.append(ram)

    elif kind == "storage":
        patterns = [
            r"\b(\d{2,4})\s*gb\s*(?:storage|internal\s+storage|rom)\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.I):
                value = int(match.group(1))
                if value not in values:
                    values.append(value)

        # Common commerce shorthand: 8GB+128GB.
        for match in re.finditer(
            r"\b(\d{1,3})\s*gb\s*\+\s*(\d{2,4})\s*gb\b",
            text,
            flags=re.I,
        ):
            ram = int(match.group(1))
            storage = int(match.group(2))

            if ram <= 64 and storage >= 32 and storage not in values:
                values.append(storage)

        # Common marketplace variant titles:
        #
        #   (Black, 128 GB) (8 GB RAM)
        #   Violet, 256 GB, 8 GB RAM
        #
        # A standalone capacity >= 32GB is treated as storage only when
        # it is NOT immediately labelled as RAM/virtual/dynamic memory.
        #
        # This keeps 8 GB RAM out of the storage signal while allowing
        # retailer variant capacities such as 128 GB / 256 GB.
        for match in re.finditer(
            r"\b(\d{2,4})\s*gb\b",
            text,
            flags=re.I,
        ):
            storage = int(match.group(1))

            if storage < 32:
                continue

            tail = text[match.end():match.end() + 30]

            if re.match(
                r"\s*(?:physical\s+)?ram\b|"
                r"\s*(?:virtual|dynamic|extended)\s+ram\b",
                tail,
                re.I,
            ):
                continue

            if storage not in values:
                values.append(storage)

    # Common marketplace shorthand:
    # "(6GB, 128GB)" or "(8GB, 256GB)"
    #
    # In phone/tablet commerce titles the smaller first capacity
    # represents RAM and the larger second capacity represents storage.
    for match in re.finditer(
        r"[\(\[]\s*(\d{1,3})\s*gb\s*,\s*(\d{2,4})\s*gb\s*[\)\]]",
        text,
        flags=re.I,
    ):
        first = int(match.group(1))
        second = int(match.group(2))

        if first <= 64 and second >= 32:
            value = first if kind == "ram" else second

            if value not in values:
                values.append(value)

    return values


def _required_capacity(
    must_have: list[str],
    suffix: str,
) -> int | None:
    for requirement in must_have:
        match = re.fullmatch(
            rf"(\d+)gb_{re.escape(suffix)}",
            clean(requirement).lower(),
        )
        if match:
            return int(match.group(1))

    return None



def tv_requirement_gate(
    title: str,
    intent: dict[str, Any],
) -> dict[str, Any]:
    requirements = intent.get("tv_requirements", {})
    if not isinstance(requirements, dict) or not requirements:
        return {
            "decision": "unknown",
            "reasons": [],
        }

    text = clean(title).lower()
    reasons = []
    contradictions = []

    # Reject obvious TV accessories before evaluating TV specs.
    tv_accessory_terms = (
        "remote compatible",
        "remote control",
        "replacement remote",
        "tv remote",
        "wall mount",
        "wall bracket",
        "tv stand",
        "replacement stand",
        "screen protector",
        "tv cover",
        "motherboard",
        "power board",
        "backlight strip",
    )

    if any(term in text for term in tv_accessory_terms):
        return {
            "decision": "reject",
            "reasons": ["TV accessory/replacement part, not a television"],
        }

    required_size = requirements.get("screen_size_inches")

    if required_size:
        sizes = [
            int(x)
            for x in re.findall(
                r"\b(32|40|42|43|48|50|55|58|60|65|70|75|77|83|85|86|98|100)"
                r"\s*(?:inch|inches|in|\\?\")\b",
                text,
                re.I,
            )
        ]

        if sizes:
            if int(required_size) in sizes:
                reasons.append(
                    f"screen size matches requested {required_size} inch"
                )
            else:
                contradictions.append(
                    f"requires {required_size} inch but title shows "
                    + "/".join(str(x) for x in sorted(set(sizes)))
                    + " inch"
                )

    required_panel = clean(requirements.get("panel_technology")).lower()

    if required_panel:
        detected_panel = None

        if re.search(r"\b(?:mini[\s-]?led|miniled)\b", text):
            detected_panel = "mini_led"
        elif re.search(r"\boled\b", text):
            detected_panel = "oled"
        elif re.search(r"\bqled\b", text):
            detected_panel = "qled"
        elif re.search(r"\bqned\b", text):
            detected_panel = "qned"
        elif re.search(r"\bcrystal(?:\s+uhd)?\b", text):
            detected_panel = "crystal_led"
        elif re.search(r"\bled\b", text):
            detected_panel = "led"

        if detected_panel:
            if detected_panel == required_panel:
                reasons.append(
                    f"panel technology matches requested {required_panel}"
                )
            else:
                contradictions.append(
                    f"requires {required_panel} but title indicates {detected_panel}"
                )

    if contradictions:
        return {
            "decision": "reject",
            "reasons": contradictions,
        }

    if reasons:
        return {
            "decision": "verified",
            "reasons": reasons,
        }

    return {
        "decision": "unknown",
        "reasons": [],
    }


def category_accessory_gate(
    title: str,
    category: str,
) -> dict[str, Any]:
    """
    Conservative category-mismatch gate.

    Reject obvious accessories/replacement parts when the user is
    shopping for the primary product itself. Generic words such as
    "display" alone are not enough to reject a smartphone.
    """
    text = normalize_key(title)
    category_text = normalize_key(category)

    # ---------------------------------------------------------
    # Television category mismatch gate.
    # Reject obvious phones, tablets and TV accessories when
    # the shopper is looking for an actual television.
    # ---------------------------------------------------------
    if category_text == "television":
        television_mismatch_patterns = (
            r"\bsmartphone\b",
            r"\bmobile\b",
            r"\bgalaxy\s+[amfsz]\d",
            r"\btablet\b",
            r"\bgalaxy\s+tab\b",
            r"\bkeyboard\s+case\b",
            r"\bphone\s+case\b",
            r"\bmobile\s+case\b",
            r"\bscreen\s+protector\b",
            r"\breplacement\s+remote\b",
            r"\bremote\s+control\b",
            r"\bwall\s+mount\b",
            r"\btv\s+stand\b",
        )

        for pattern in television_mismatch_patterns:
            if re.search(pattern, text, re.I):
                return {
                    "status": "reject",
                    "reason": (
                        "Obvious non-television product/accessory "
                        "detected in product title"
                    ),
                }

        return {
            "status": "pass",
            "reason": "No explicit television category mismatch",
        }

    if category_text not in {
        "smartphone",
        "phone",
        "mobile",
        "mobile phone",
    }:
        return {
            "status": "pass",
            "reason": "No smartphone accessory gate required",
        }

    accessory_patterns = (
        r"\bdisplay\s+combo\b",
        r"\bcombo\s+folder\b",
        r"\bdisplay\s+folder\b",
        r"\blcd\s+screen\b",
        r"\bdigitizer\b",
        r"\bscreen\s+replacement\b",
        r"\breplacement\s+screen\b",
        r"\bdisplay\s+replacement\b",
        r"\breplacement\s+display\b",
        r"\bscreen\s+protector\b",
        r"\btempered\s+glass\b",
        r"\bphone\s+case\b",
        r"\bmobile\s+case\b",
        r"\bkeyboard\s+case\b",
        r"\btablet\s+case\b",
        r"\bfolio\s+cover\b",
        r"\bgalaxy\s+tab\b",
        r"\bflip\s+case\b",
        r"\bback\s+cover\b",
        r"\bprotective\s+cover\b",
        r"\bcase\s+cover\b",
        r"\bleather\s+case\b",
        r"\bcharging\s+cable\b",
        r"\bcharger\b",
        r"\bpower\s*bank\b",
        r"\bportable\s+charger\b",
        r"\btravel\s+adap(?:ter|tor)\b",
        r"\bwall\s+adap(?:ter|tor)\b",
        r"\busb\s+adap(?:ter|tor)\b",
        r"\bwireless\s+charger\b",
        r"\bcharging\s+stand\b",
        r"\bcharging\s+pad\b",
        r"\bphone\s+holder\b",
        r"\bmobile\s+holder\b",

        # Additional accessory noise commonly returned by
        # brand-scoped smartphone marketplace searches.
        r"\botg\b",
        r"\botg\s+(?:cable|adapter|adaptor|converter)\b",
        r"\bconverter\b",
        r"\bconnector\b",
        r"\bpouch\b",
        r"\bmobile\s+pouch\b",
        r"\bphone\s+pouch\b",
        r"\bskin\b",
        r"\bmobile\s+skin\b",
        r"\bphone\s+skin\b",
        r"\bback\s+skin\b",
        r"\bhard\s+back\b",
        r"\bhard\s+case\b",
        r"\bmagnetic\s+case\b",
        r"\bbumper\s+case\b",
        r"\bsilicone\s+case\b",
        r"\bclear\s+case\b",
        r"\bprotective\s+case\b",
        # Obvious adjacent electronics that can leak into broad
        # marketplace searches, especially brand-only/battery queries.
        r"\bearbuds?\b",
        r"\btws\b",
        r"\bneckband\b",
        r"\bheadphones?\b",
        r"\bsmartwatch\b",
        r"\bsmart\s+watch\b",
        r"\btablet\b",
        r"\btelevision\b",
        r"\bsmart\s+tv\b",
        r"\brefrigerator\b",
        r"\bwashing\s+machine\b",
    )

    for pattern in accessory_patterns:
        if re.search(pattern, text, re.I):
            return {
                "status": "reject",
                "reason": (
                    "Obvious smartphone accessory/replacement part "
                    "detected in product title"
                ),
            }

    return {
        "status": "pass",
        "reason": "No explicit smartphone accessory evidence",
    }


def discovery_variant_gate(
    title: str,
    intent: dict[str, Any],
) -> dict[str, Any]:
    """
    Early contradiction gate only.

    PASS    = explicit title evidence satisfies requirement.
    REJECT  = explicit title evidence contradicts requirement.
    UNKNOWN = title does not contain enough evidence.

    UNKNOWN must continue downstream for official verification.
    """
    must_have = list(intent.get("must_have") or [])

    required_ram = _required_capacity(must_have, "ram")
    required_storage = _required_capacity(must_have, "storage")

    ram_values = _capacity_values_from_title(title, "ram")
    storage_values = _capacity_values_from_title(title, "storage")

    reasons: list[str] = []
    contradictions: list[str] = []
    confirmed: list[str] = []

    if required_ram is not None:
        if ram_values:
            if max(ram_values) >= required_ram:
                confirmed.append(
                    f"RAM satisfies at least {required_ram}GB"
                )
            else:
                contradictions.append(
                    f"requires at least {required_ram}GB RAM; "
                    f"title explicitly shows {ram_values}GB"
                )
        else:
            reasons.append("RAM capacity not explicit in title")

    if required_storage is not None:
        if storage_values:
            if max(storage_values) >= required_storage:
                confirmed.append(
                    f"Storage satisfies at least {required_storage}GB"
                )
            else:
                contradictions.append(
                    f"requires at least {required_storage}GB storage; "
                    f"title explicitly shows {storage_values}GB"
                )
        else:
            reasons.append("Storage capacity not explicit in title")

    if contradictions:
        status = "reject"
    elif (
        (required_ram is None or (ram_values and max(ram_values) >= required_ram))
        and
        (
            required_storage is None
            or (
                storage_values
                and max(storage_values) >= required_storage
            )
        )
    ):
        status = "pass"
    else:
        status = "unknown"

    return {
        "status": status,
        "required_ram_gb": required_ram,
        "required_storage_gb": required_storage,
        "observed_ram_gb": ram_values,
        "observed_storage_gb": storage_values,
        "confirmed": confirmed,
        "contradictions": contradictions,
        "notes": reasons,
    }


def discover_market(
    user_query: str,
    max_candidates: int = 20,
    live_fast: bool = False,
) -> dict[str, Any]:
    intent = parse_query(user_query)
    category = intent.get("category")
    queries = build_discovery_queries(user_query, intent)

    # Visitor requests must keep discovery latency bounded.
    # Deep/offline mode still uses the full discovery query set.
    #
    # For RAM/storage-specific smartphone searches, blindly taking the
    # first two queries wastes both live slots on near-duplicates.
    # Prefer:
    #   1. one retailer-friendly exact capacity representation
    #   2. one broad brand/category/budget fallback
    #
    # Downstream variant/evidence gates remain strict, so this increases
    # discovery recall without relaxing recommendation correctness.
    if live_fast and len(queries) > 2:
        live_queries: list[str] = []

        # If the shopper explicitly names an alphanumeric product model,
        # reserve the first live discovery slot for the query that preserves
        # that exact model token. This improves recall without weakening any
        # downstream identity, variant, evidence, or recommendation gate.
        query_key_for_live_model = normalize_key(user_query)

        live_model_tokens = {
            token
            for token in query_key_for_live_model.split()
            if re.search(r"[a-z]", token)
            and re.search(r"\d", token)
            and token not in {"5g", "4g", "3g", "2g"}
            and not re.fullmatch(
                r"\d+(?:\.\d+)?"
                r"(?:gb|tb|mb|mah|hz|khz|mhz|ghz|mp|w|kw|v|inch|inches|cm|mm)",
                token,
                re.I,
            )
        }

        if live_model_tokens:
            named_model_query = next(
                (
                    query
                    for query in queries
                    if live_model_tokens.issubset(
                        set(normalize_key(query).split())
                    )
                ),
                None,
            )

            if named_model_query:
                live_queries.append(named_model_query)

        must_have_values = {
            clean(value).lower()
            for value in intent.get("must_have", [])
            if clean(value)
        }

        has_ram_requirement = any(
            re.fullmatch(r"\d+gb_ram", value)
            for value in must_have_values
        )
        has_storage_requirement = any(
            re.fullmatch(r"\d+gb_storage", value)
            for value in must_have_values
        )

        if (
            category == "smartphone"
            and has_ram_requirement
            and has_storage_requirement
        ):
            # Prefer the clean retailer-style brand/family/capacity
            # query when available. This avoids noisy terms such as
            # "under", "India" and "buy" reducing exact variant recall.
            specialist = next(
                (
                    query
                    for query in queries
                    if re.search(
                        r"\b\d{2,4}gb\b.*\b\d{1,3}gb\s+ram\b",
                        query,
                        re.I,
                    )
                    and "india" not in query.lower()
                    and "under" not in query.lower()
                    and "buy" not in query.lower()
                ),
                None,
            )

            if specialist is None:
                specialist = next(
                    (
                        query
                        for query in queries
                        if re.search(
                            r"\b\d{1,3}gb\+\d{2,4}gb\b",
                            query,
                            re.I,
                        )
                    ),
                    None,
                )

            # Broad fallback should preserve brand/category/budget but
            # not force a particular capacity representation.
            broad = next(
                (
                    query
                    for query in queries
                    if "ram" not in query.lower()
                    and "storage" not in query.lower()
                    and not re.search(
                        r"\b\d{1,3}gb\+\d{2,4}gb\b",
                        query,
                        re.I,
                    )
                ),
                None,
            )

            for query in (specialist, broad):
                if query and query not in live_queries:
                    live_queries.append(query)

        # Generic categories / queries keep the original fast behavior.
        for query in queries:
            if len(live_queries) >= 2:
                break

            if query not in live_queries:
                live_queries.append(query)

        queries = live_queries[:2]

    api_key = os.environ.get("TAVILY_API_KEY")

    client = (
        TavilyClient(api_key=api_key)
        if api_key
        else None
    )

    tavily_available = client is not None
    provider_errors: list[str] = []

    raw: list[dict[str, Any]] = []

    for query in queries:

        commerce_results: list[dict[str, Any]] = []
        open_web_results: list[dict[str, Any]] = []

        if tavily_available and client is not None:

            try:
                commerce_results = search_channel(
                    client,
                    query=query,
                    category=category,
                    include_domains=COMMERCE_DOMAINS,
                    channel="commerce",
                    max_results=20,
                )

                open_web_results = search_channel(
                    client,
                    query=query,
                    category=category,
                    include_domains=None,
                    channel="open_web",
                    max_results=15,
                )

            except Exception as error:

                message = str(error)
                provider_errors.append(message)

                lowered = message.lower()

                if (
                    "usage limit" in lowered
                    or "quota" in lowered
                    or "rate limit" in lowered
                    or "resource_exhausted" in lowered
                    or "upgrade your plan" in lowered
                ):
                    tavily_available = False

                commerce_results = []
                open_web_results = []

        # Coupon World's local knowledge + Amazon exact-ASIN search-card
        # lane supplements general commerce discovery rather than running
        # only when Tavily returns zero results.
        #
        # This keeps discovery-provider relevance separate from evidence
        # quality: downstream identity, variant and evidence gates still
        # decide what is trustworthy and final Fit remains unaffected.
        supplementary_commerce_results = fallback_search_channel(
            query=query,
            category=category,
            include_domains=COMMERCE_DOMAINS,
            channel="commerce",
            max_results=20,
        )

        commerce_results.extend(supplementary_commerce_results)

        if not open_web_results:

            open_web_results = fallback_search_channel(
                query=query,
                category=category,
                include_domains=None,
                channel="open_web",
                max_results=15,
            )

        raw.extend(commerce_results)
        raw.extend(open_web_results)

    ranked: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # EXACT NAMED-MODEL DISCOVERY GATE
    # ---------------------------------------------------------
    # When the shopper explicitly names an alphanumeric model,
    # sibling models must be removed BEFORE ranking/truncation.
    #
    # Examples:
    # Samsung Galaxy F36 5G -> require F36
    # Motorola G86 -> require G86
    #
    # Generic queries such as "best phone under 20000" or
    # "8/128 phone under 20k" remain unrestricted.
    query_key_for_model = normalize_key(user_query)

    def is_capacity_or_unit_token(token: str) -> bool:
        """
        Exclude shopper specification tokens from exact model locking.

        Examples:
        - 8gb / 12gb RAM
        - 128gb / 256gb / 512gb storage
        - 1tb storage
        - 5000mah battery
        - 120hz refresh rate

        True model tokens such as F36, A23, S24 and G86 remain eligible.
        """
        token = str(token or "").lower().strip()

        if not token:
            return False

        return bool(
            re.fullmatch(
                r"\d+(?:\.\d+)?"
                r"(?:gb|tb|mb|mah|hz|khz|mhz|ghz|mp|w|kw|v|inch|inches|cm|mm)",
                token,
                re.I,
            )
        )

    exact_query_model_tokens = {
        token
        for token in query_key_for_model.split()
        if re.search(r"[a-z]", token)
        and re.search(r"\d", token)
        and token not in {"5g", "4g", "3g", "2g"}
        and not is_capacity_or_unit_token(token)
    }

    # Brand semantics must distinguish REQUIRED, PREFERRED and AVOIDED.
    # `intent["brands"]` is detection metadata and includes all mentioned
    # brands, so treating it as a hard filter breaks queries such as
    # "Samsung preferred" and "Samsung nahi chahiye".
    mentioned_brands = [
        normalize_key(brand)
        for brand in intent.get("brands", [])
        if normalize_key(brand)
    ]
    must_markers = {
        normalize_key(x)
        for x in intent.get("must_have", [])
        if normalize_key(x)
    }
    preferred_markers = {
        normalize_key(x)
        for x in intent.get("preferred", [])
        if normalize_key(x)
    }
    avoid_markers = {
        normalize_key(x)
        for x in intent.get("avoid", [])
        if normalize_key(x)
    }

    required_brands = []
    avoided_brands = []

    for brand in mentioned_brands:
        marker = normalize_key(f"brand_{brand}")

        if marker in avoid_markers:
            avoided_brands.append(brand)
            continue

        if marker in must_markers:
            required_brands.append(brand)
            continue

        # A bare brand query (e.g. "Samsung phone under 25k") is a
        # brand-scoped request. An explicitly preferred brand remains soft.
        if marker not in preferred_markers:
            required_brands.append(brand)

    for item in raw:
        title = compact_product_title(item["title"])

        if is_generic_listing_title(title):
            continue

        normalized_title = normalize_key(title)

        # Exact named-model queries must not allow sibling models to
        # consume the limited candidate slots.
        if exact_query_model_tokens:
            title_tokens = set(normalized_title.split())

            if not exact_query_model_tokens.issubset(title_tokens):
                continue

        # Explicit/bare brand scope is hard. Preferred brands are ranked
        # downstream and therefore must not narrow discovery.
        #
        # Marketplace titles sometimes omit the manufacturer name while
        # retaining a distinctive product-family identity. Example:
        #   "Galaxy A17 5G ..." instead of "Samsung Galaxy A17 5G ..."
        #
        # Accept a small conservative set of strong family aliases rather
        # than weakening the brand gate globally.
        def title_matches_required_brand(brand: str) -> bool:
            if re.search(
                rf"(?:^|\s){re.escape(brand)}(?:\s|$)",
                normalized_title,
            ):
                return True

            # Amazon frequently omits "Samsung" from genuine Galaxy
            # phone titles. Do not treat the word "Galaxy" alone as
            # Samsung evidence because unrelated products such as
            # "Gesto Galaxy Projector" would leak through.
            if brand == "samsung":
                return bool(
                    re.search(
                        r"\bgalaxy\s+(?:"
                        r"[amfs]\s*\d{1,3}[a-z]*"
                        r"|z\s*(?:fold|flip)\s*\d*[a-z]*"
                        r")\b",
                        normalized_title,
                        re.I,
                    )
                )

            return False

        if required_brands and not any(
            title_matches_required_brand(brand)
            for brand in required_brands
        ):
            continue

        # Explicit negative brand semantics are a hard exclusion.
        if avoided_brands and any(
            re.search(
                rf"(?:^|\s){re.escape(brand)}(?:\s|$)",
                normalized_title,
            )
            for brand in avoided_brands
        ):
            continue

        accessory_gate = category_accessory_gate(
            title,
            category,
        )

        if accessory_gate["status"] == "reject":
            continue

        tv_gate = {
            "decision": "unknown",
            "reasons": [],
        }

        if category == "television":
            tv_gate = tv_requirement_gate(
                title,
                intent,
            )

            # Reject only explicit contradictions.
            # Missing title evidence remains eligible for downstream
            # verification rather than being treated as a failure.
            if tv_gate.get("decision") == "reject":
                continue

        variant_gate = discovery_variant_gate(
            title,
            intent,
        )

        # Discovery is allowed to reject only explicit contradictions.
        # Missing title evidence remains eligible for official verification.
        if variant_gate["status"] == "reject":
            continue

        enriched = dict(item)
        enriched["clean_title"] = title
        enriched["known_brand"] = known_brand_from_title(title)
        enriched["quality_score"] = candidate_quality_score(item, title)
        enriched["variant_gate"] = variant_gate
        enriched["tv_requirement_gate"] = tv_gate

        ranked.append(enriched)

    # Quality-aware discovery ranking.
    # Known brand is supportive evidence, never a hard requirement.
    # Variant-aware discovery ranking.
    #
    # Explicitly confirmed shopper requirements must outrank candidates
    # whose title does not provide enough variant evidence.
    #
    # PASS    -> strongest discovery priority
    # UNKNOWN -> remains eligible for downstream verification
    # REJECT  -> already removed above
    #
    # This does not convert discovery evidence into final recommendation
    # Fit. It only prevents an unknown variant from crowding out an
    # explicitly matching variant before max_candidates truncation.
    variant_priority = {
        "pass": 2,
        "unknown": 1,
        "reject": 0,
    }

    def named_model_evidence_priority(
        item: dict[str, Any],
    ) -> int:
        """
        Prefer stronger commerce evidence only for an explicit named-model
        query after the strict model/variant gates have already passed.

        This is discovery evidence priority, not product Fit and not a
        retailer preference.
        """
        if not exact_query_model_tokens:
            return 0

        title_text = clean(item.get("clean_title") or item.get("title"))

        # Do not let protection/warranty/service bundles become the primary
        # handset evidence merely because they expose an ASIN and price.
        if re.search(
            r"\b(?:care services|damage protection|protection plan|"
            r"extended warranty|warranty plan)\b",
            title_text,
            re.I,
        ):
            return 0

        asin = clean(item.get("asin"))
        price_text = clean(item.get("search_price_text"))
        method = clean(item.get("search_price_evidence_method"))

        if asin and price_text and method:
            return 2

        if asin:
            return 1

        return 0

    ranked.sort(
        key=lambda item: (
            variant_priority.get(
                clean(
                    (item.get("variant_gate") or {}).get("status")
                ).lower(),
                1,
            ),
            named_model_evidence_priority(item),
            item["quality_score"],
            item["search_score"],
        ),
        reverse=True,
    )

    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for item in ranked:
        title = item["clean_title"]
        title_key = normalize_key(title)
        url = item["url"]

        if not title_key or url in seen_urls:
            continue

        if title_key in seen_titles:
            continue

        seen_urls.add(url)
        seen_titles.add(title_key)

        candidates.append(
            {
                "candidate_id": f"market-{len(candidates)+1:02d}",
                "title": title,
                "source_title": item["title"],
                "source_url": url,
                "source_host": item["host"],
                "discovery_channel": item["channel"],
                "discovered_by_query": item["query"],
                "discovery_score": round(item["search_score"], 4),
                "discovery_quality_score": item["quality_score"],
                "known_brand": item["known_brand"],
                "snippet": item["content"],
                "provider": item.get("provider"),
                "asin": item.get("asin"),
                "search_image": item.get("search_image"),
                "search_price_text": item.get("search_price_text"),
                "search_price_currency": item.get(
                    "search_price_currency"
                ),
                "search_price_evidence_method": item.get(
                    "search_price_evidence_method"
                ),
                "variant_gate": item.get("variant_gate"),
                "tv_requirement_gate": item.get("tv_requirement_gate"),
                "status": "discovered_unverified",
            }
        )

        if len(candidates) >= max_candidates:
            break

    return {
        "query": user_query,
        "intent": intent,
        "discovery_queries": queries,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "note": (
            "Discovery quality scores only prioritize candidate research; "
            "final recommendation Fit must be computed from verified evidence."
        ),
    }

def print_result(payload: dict[str, Any]) -> None:
    print("=" * 76)
    print("COUPON WORLD MARKET DISCOVERY ENGINE v1.6.1")
    print("=" * 76)
    print("QUERY:", payload.get("query"))
    print("CATEGORY:", payload.get("intent", {}).get("category"))
    print("DISCOVERY QUERIES:")

    for query in payload.get("discovery_queries", []):
        print("  -", query)

    print()
    print("CANDIDATES:", payload.get("candidate_count"))
    print()

    for i, candidate in enumerate(payload.get("candidates", []), 1):
        print("-" * 76)
        print(f"#{i} | {candidate.get('title')}")
        print("CHANNEL:", candidate.get("discovery_channel"))
        print("HOST   :", candidate.get("source_host"))
        print("URL    :", candidate.get("source_url"))
        print("SCORE  :", candidate.get("discovery_score"))
        print("STATE  :", candidate.get("status"))

    print()
    print(payload.get("note"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover real product-detail candidates from the market"
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--max-candidates", type=int, default=20)
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        payload = discover_market(
            args.query,
            max_candidates=max(3, min(args.max_candidates, 30)),
        )
    except Exception as error:
        print("ERROR:", str(error))
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_result(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

