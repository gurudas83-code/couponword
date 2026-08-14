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
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

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
    category = clean(intent.get("category"))
    budget = intent.get("budget_max")

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

    must_have = [
        clean(x).replace("_", " ")
        for x in intent.get("must_have", [])
        if clean(x)
    ]

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

def fallback_search_channel(
    *,
    query: str,
    category: str | None,
    include_domains: list[str] | None,
    channel: str,
    max_results: int,
) -> list[dict[str, Any]]:
    """
    Free discovery fallback using the existing DuckDuckGo HTML
    search helper.

    Existing product-result validation remains authoritative.
    """

    domains: list[str] = []

    if include_domains:
        domains.extend(include_domains)

    # Open-web fallback should still remain commerce/product oriented.
    # Include known official brand domains as secondary discovery sources.
    if channel == "open_web":
        for values in BRAND_DOMAINS.values():
            for domain in values:
                if domain not in domains:
                    domains.append(domain)

    if not domains:
        domains = list(COMMERCE_DOMAINS)

    # DuckDuckGo HTML is currently disabled as a runtime provider.
    # It has proven too unreliable/slow for unattended batch discovery.
    # Keep this adapter in place so a better free provider can be wired
    # here later without touching downstream ranking logic.
    return []

    accepted: list[dict[str, Any]] = []

    for result in raw_results:

        if not isinstance(result, dict):
            continue

        title = clean(result.get("title"))
        url = clean(result.get("url"))

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
                "content": clean(
                    result.get("content")
                ),
                "search_score": float(
                    result.get("score") or 0
                ),
                "query": query,
                "channel": channel,
                "provider": "duckduckgo_html",
            }
        )

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


def discover_market(
    user_query: str,
    max_candidates: int = 20,
) -> dict[str, Any]:
    intent = parse_query(user_query)
    category = intent.get("category")
    queries = build_discovery_queries(user_query, intent)

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

        if not commerce_results:

            commerce_results = fallback_search_channel(
                query=query,
                category=category,
                include_domains=COMMERCE_DOMAINS,
                channel="commerce",
                max_results=20,
            )

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

    for item in raw:
        title = compact_product_title(item["title"])

        if is_generic_listing_title(title):
            continue

        enriched = dict(item)
        enriched["clean_title"] = title
        enriched["known_brand"] = known_brand_from_title(title)
        enriched["quality_score"] = candidate_quality_score(item, title)

        ranked.append(enriched)

    # Quality-aware discovery ranking.
    # Known brand is supportive evidence, never a hard requirement.
    ranked.sort(
        key=lambda item: (
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
