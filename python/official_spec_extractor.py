#!/usr/bin/env python3
"""
Coupon World Official Specification Extractor v2.0

Reads official product URLs from data/research_results.json, downloads
public manufacturer pages, extracts review-ready specifications and
writes data/official_specs.json.

It does not publish extracted data automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as error:
    raise SystemExit(
        "Missing packages. Run: py -m pip install requests beautifulsoup4 lxml"
    ) from error


ROOT = Path(__file__).resolve().parent.parent
RESEARCH_RESULTS_DB = ROOT / "data" / "research_results.json"
IDENTITY_DB = ROOT / "data" / "intelligence" / "product_identity_v2.json"
OUTPUT_DB = ROOT / "data" / "official_specs.json"

USER_AGENT = (
    "Mozilla/5.0 (compatible; CouponWorldResearch/1.0; "
    "+https://coupon-world.in/)"
)
TIMEOUT = 20
MAX_RETRIES = 2
DELAY_SECONDS = 1.0
MAX_FEATURES = 80
MAX_SPECS = 120

NOISE_PHRASES = (
    "cookie",
    "privacy policy",
    "terms and conditions",
    "sign in",
    "login",
    "register",
    "subscribe",
    "newsletter",
    "add to cart",
    "buy now",
    "copyright",
    "more products",
    "compare",
    "exclusive offers",
    "realme coins",
    "vip benefits",
    "declaration and disclosure",
    "full range of products",
    "latest updates",
    "select country",
    "select region",
)

FEATURE_HINTS = (
    "battery",
    "playback",
    "charging",
    "bluetooth",
    "wireless",
    "driver",
    "microphone",
    "noise cancellation",
    "anc",
    "enc",
    "latency",
    "water resistant",
    "dust resistant",
    "ip",
    "weight",
    "height",
    "width",
    "depth",
    "dimension",
    "compatib",
    "frequency",
    "touch control",
    "sensor",
    "range",
    "warranty",
    "processor",
    "display",
    "storage",
    "ram",
    "camera",
    "resolution",
    "refresh rate",
    "material",
    "type-c",
    "usb",
)

COUNTRY_CURRENCY_PATTERN = re.compile(
    r"\b(?:india|indonesia|vietnam|thailand|malaysia|philippines|"
    r"singapore|pakistan|bangladesh|cambodia|sri lanka|kazakhstan|"
    r"uzbekistan|russia|czech republic|united kingdom|ukraine|belarus|"
    r"bulgaria|south africa|saudi arabia|colombia|brasil|honduras|"
    r"costa rica)\b.*\b(?:inr|idr|vnd|thb|myr|php|sgd|pkr|bdt|usd|"
    r"lkr|uzs|rub|czk|gbp|uah|byn|bgn|zar|sar|brl|hnl|crc)\b",
    re.IGNORECASE,
)

UNWANTED_URL_PARTS = (
    "youtube.com",
    "youtu.be",
    "apps.apple.com",
    "play.google.com",
    "/newsroom/",
    "/press-release",
    "/blog/",
    "/community/",
    "/post-details/",
    "c.realme.com/",
)

ALIASES = {
    "battery life": "battery_life",
    "battery": "battery",
    "charging": "charging",
    "fast charging": "charging",
    "bluetooth": "bluetooth",
    "wireless technology": "wireless",
    "wireless": "wireless",
    "operating system": "operating_system",
    "os": "operating_system",
    "compatibility": "compatibility",
    "system requirements": "compatibility",
    "dimensions": "dimensions",
    "dimension": "dimensions",
    "weight": "weight",
    "warranty": "warranty",
    "driver": "driver",
    "driver size": "driver",
    "frequency response": "frequency_response",
    "microphone": "microphone",
    "noise cancellation": "noise_cancellation",
    "anc": "noise_cancellation",
    "water resistance": "water_resistance",
    "ip rating": "water_resistance",
    "display": "display",
    "display size": "display_size",
    "screen size": "display_size",
    "resolution": "resolution",
    "refresh rate": "refresh_rate",
    "processor": "processor",
    "chipset": "processor",
    "ram": "ram",
    "memory": "memory",
    "storage": "storage",
    "camera": "camera",
    "rear camera": "rear_camera",
    "front camera": "front_camera",
    "connectivity": "connectivity",
    "ports": "ports",
    "material": "material",
    "color": "color",
    "model": "model",
    "model number": "model_number",
    "product type": "product_type",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value: Any) -> str:
    key = clean_text(value).lower()
    key = re.sub(r"[:：]+$", "", key)
    key = re.sub(r"[^a-z0-9\s/+&-]", " ", key)
    key = re.sub(r"\s+", " ", key).strip()

    if key in ALIASES:
        return ALIASES[key]

    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")


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


def load_identity_index() -> dict[str, dict[str, Any]]:
    payload = load_json(IDENTITY_DB, {"identities": []})
    identities = payload.get("identities", []) if isinstance(payload, dict) else []
    index: dict[str, dict[str, Any]] = {}

    if isinstance(identities, list):
        for identity in identities:
            if not isinstance(identity, dict):
                continue

            product_id = identity.get("product_id")

            if product_id not in (None, ""):
                index[str(product_id)] = identity

    return index


def is_unwanted_url(url: str) -> bool:
    lowered = url.lower()
    return any(part in lowered for part in UNWANTED_URL_PARTS)


def hostname(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def fetch_page(url: str) -> tuple[str | None, str | None, int | None]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    last_error: str | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=TIMEOUT,
                allow_redirects=True,
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "").lower()

                if "html" not in content_type and "xhtml" not in content_type:
                    return None, f"Unsupported content type: {content_type}", response.status_code

                response.encoding = response.apparent_encoding or response.encoding
                return response.text, None, response.status_code

            last_error = f"HTTP {response.status_code}"

            if response.status_code in {401, 403, 404}:
                break

        except requests.RequestException as error:
            last_error = str(error)

        if attempt < MAX_RETRIES:
            time.sleep(1.5 * (attempt + 1))

    return None, last_error or "Unknown fetch error", None


def parse_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(" ", strip=True)

        if not raw:
            continue

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        stack: list[Any] = [payload]

        while stack:
            current = stack.pop()

            if isinstance(current, list):
                stack.extend(current)
                continue

            if not isinstance(current, dict):
                continue

            graph = current.get("@graph")

            if isinstance(graph, list):
                stack.extend(graph)

            item_type = current.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]

            if any(
                str(value).lower()
                in {"product", "individualproduct", "productmodel"}
                for value in types
                if value
            ):
                items.append(current)

    return items


def extract_meta(soup: BeautifulSoup) -> dict[str, str]:
    result: dict[str, str] = {}

    if soup.title:
        result["html_title"] = clean_text(soup.title.get_text(" ", strip=True))

    for key, attribute, value in (
        ("description", "name", "description"),
        ("og_title", "property", "og:title"),
        ("og_description", "property", "og:description"),
    ):
        tag = soup.find("meta", attrs={attribute: value})

        if tag and tag.get("content"):
            result[key] = clean_text(tag.get("content"))

    canonical = soup.find("link", attrs={"rel": "canonical"})

    if canonical and canonical.get("href"):
        result["canonical_url"] = clean_text(canonical.get("href"))

    h1 = soup.find("h1")

    if h1:
        result["h1"] = clean_text(h1.get_text(" ", strip=True))

    return result


def add_specification(
    specifications: dict[str, dict[str, Any]],
    key: str,
    value: str,
    source: str,
    confidence: int,
) -> None:
    normalized_key = normalize_key(key)
    normalized_value = clean_text(value)

    if not normalized_key or not normalized_value:
        return

    if len(normalized_value) > 500:
        return

    existing = specifications.get(normalized_key)
    record = {
        "value": normalized_value,
        "label": clean_text(key),
        "source": source,
        "confidence": confidence,
    }

    if existing is None or confidence > int(existing.get("confidence") or 0):
        specifications[normalized_key] = record


def extract_tables(
    soup: BeautifulSoup,
    specifications: dict[str, dict[str, Any]],
) -> int:
    before = len(specifications)

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])

            if len(cells) < 2:
                continue

            add_specification(
                specifications,
                cells[0].get_text(" ", strip=True),
                " | ".join(cell.get_text(" ", strip=True) for cell in cells[1:]),
                "html_table",
                95,
            )

    return len(specifications) - before


def extract_definition_lists(
    soup: BeautifulSoup,
    specifications: dict[str, dict[str, Any]],
) -> int:
    before = len(specifications)

    for definition_list in soup.find_all("dl"):
        for term in definition_list.find_all("dt"):
            description = term.find_next_sibling("dd")

            if description is None:
                continue

            add_specification(
                specifications,
                term.get_text(" ", strip=True),
                description.get_text(" ", strip=True),
                "definition_list",
                92,
            )

    return len(specifications) - before


def extract_json_ld_specs(
    products: list[dict[str, Any]],
    specifications: dict[str, dict[str, Any]],
) -> int:
    before = len(specifications)

    for product in products:
        for key in (
            "name",
            "model",
            "sku",
            "mpn",
            "brand",
            "color",
            "material",
            "size",
            "weight",
            "description",
        ):
            value = product.get(key)

            if isinstance(value, dict):
                value = value.get("name") or value.get("value")

            if isinstance(value, (str, int, float)):
                add_specification(
                    specifications,
                    key,
                    str(value),
                    "json_ld",
                    90,
                )

        additional = product.get("additionalProperty")

        if isinstance(additional, list):
            for item in additional:
                if not isinstance(item, dict):
                    continue

                name = item.get("name") or item.get("propertyID")
                value = item.get("value")

                if name and value not in (None, ""):
                    add_specification(
                        specifications,
                        str(name),
                        str(value),
                        "json_ld_additional_property",
                        94,
                    )

    return len(specifications) - before


def extract_label_value_blocks(
    soup: BeautifulSoup,
    specifications: dict[str, dict[str, Any]],
) -> int:
    before = len(specifications)

    for selector in (
        "[class*='spec']",
        "[class*='detail']",
        "[class*='feature']",
        "[class*='attribute']",
        "[class*='tech']",
    ):
        for node in soup.select(selector):
            text = clean_text(node.get_text(" ", strip=True))

            if not text or len(text) > 400:
                continue

            match = re.match(
                r"^([A-Za-z][A-Za-z0-9 /+&()._-]{1,55})\s*[:：]\s*(.{2,300})$",
                text,
            )

            if match:
                add_specification(
                    specifications,
                    match.group(1),
                    match.group(2),
                    "label_value_block",
                    78,
                )

    return len(specifications) - before


def remove_page_chrome(soup: BeautifulSoup) -> None:
    """Remove navigation, footer and other page-wide noise before extraction."""
    for selector in (
        "nav",
        "header",
        "footer",
        "aside",
        "[role='navigation']",
        "[role='banner']",
        "[role='contentinfo']",
        "[class*='cookie']",
        "[id*='cookie']",
        "[class*='breadcrumb']",
        "[class*='country']",
        "[class*='region']",
        "[class*='locale']",
        "[class*='language']",
        "[class*='newsletter']",
        "[class*='recommend']",
        "[class*='related-product']",
        "[class*='product-nav']",
        "[class*='menu']",
    ):
        for node in soup.select(selector):
            node.decompose()


def is_noise_feature(text: str) -> bool:
    lowered = text.lower()

    if any(phrase in lowered for phrase in NOISE_PHRASES):
        return True

    if COUNTRY_CURRENCY_PATTERN.search(text):
        return True

    if lowered.startswith("new ") and len(text.split()) <= 8:
        return True

    # Menu-like short product names without any technical information.
    if (
        len(text.split()) <= 8
        and any(
            brand_word in lowered
            for brand_word in ("realme", "redmi", "xiaomi", "iphone", "narzo")
        )
        and not any(hint in lowered for hint in FEATURE_HINTS)
    ):
        return True

    return False


def feature_relevance_score(text: str) -> int:
    lowered = text.lower()
    score = sum(1 for hint in FEATURE_HINTS if hint in lowered)

    # Numeric units are strong signs of a real specification.
    if re.search(
        r"\\b\\d+(?:\\.\\d+)?\\s*(?:mah|wh|w|hours?|hrs?|mm|cm|g|kg|"
        r"hz|khz|mhz|ghz|mp|db|ms|meters?|m)\\b",
        lowered,
    ):
        score += 2

    if ":" in text:
        score += 1

    return score


def feature_scope(soup: BeautifulSoup) -> list[Any]:
    """Prefer the actual product/specification content over the whole page."""
    scoped_nodes: list[Any] = []

    for selector in (
        "main",
        "article",
        "[id*='spec']",
        "[class*='specification']",
        "[class*='specs']",
        "[class*='technical']",
        "[class*='product-detail']",
        "[class*='product-feature']",
    ):
        scoped_nodes.extend(soup.select(selector))

    # Avoid duplicate nested scopes while preserving order.
    unique: list[Any] = []
    seen_ids: set[int] = set()

    for node in scoped_nodes:
        node_id = id(node)

        if node_id not in seen_ids:
            seen_ids.add(node_id)
            unique.append(node)

    return unique or [soup]


def extract_features(soup: BeautifulSoup) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    seen: set[str] = set()

    for scope in feature_scope(soup):
        for node in scope.find_all(["li", "p"]):
            text = clean_text(node.get_text(" ", strip=True))

            if not (12 <= len(text) <= 300):
                continue

            if is_noise_feature(text):
                continue

            relevance = feature_relevance_score(text)

            # Keep only text that looks like a technical feature/specification.
            if relevance <= 0:
                continue

            lowered = text.lower()

            if lowered in seen:
                continue

            seen.add(lowered)
            confidence = min(
                90,
                (74 if node.name == "li" else 68) + relevance * 3,
            )

            features.append(
                {
                    "text": text,
                    "source": node.name,
                    "confidence": confidence,
                    "relevance_score": relevance,
                }
            )

    features.sort(
        key=lambda item: (
            item.get("relevance_score", 0),
            item.get("confidence", 0),
        ),
        reverse=True,
    )

    return features[:MAX_FEATURES]


def identity_tokens(value: Any) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", clean_text(value).lower())
    stop_words = {
        "official",
        "specifications",
        "specification",
        "specs",
        "features",
        "product",
        "page",
        "india",
        "global",
        "with",
        "and",
        "for",
        "the",
        "black",
        "blue",
        "white",
        "gold",
        "wireless",
        "usb",
    }

    return {
        token
        for token in tokens
        if (
            token not in stop_words
            and (
                len(token) >= 2
                or token.isdigit()
            )
        )
    }



def decode_shopify_oxygen_stream(html: str) -> str:
    """
    Return a searchable text view of Shopify Hydrogen/Oxygen
    React Router stream payloads embedded in script tags.
    """

    if "__reactRouterContext.streamController.enqueue" not in html:
        return ""

    chunks = re.findall(
        r'window\.__reactRouterContext\.streamController\.enqueue\("((?:\\.|[^"\\])*)"\)',
        html,
        flags=re.S,
    )

    if not chunks:
        return ""

    decoded_chunks: list[str] = []

    for chunk in chunks:
        try:
            decoded = bytes(chunk, "utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            decoded = chunk

        decoded = (
            decoded
            .replace("\\/", "/")
            .replace("\\u0026", "&")
            .replace("\\u003c", "<")
            .replace("\\u003e", ">")
        )

        decoded_chunks.append(decoded)

    return re.sub(r"\s+", " ", " ".join(decoded_chunks)).strip()


def add_stream_spec(
    specifications: dict[str, dict[str, Any]],
    key: str,
    label: str,
    value: str,
    confidence: int = 82,
) -> bool:
    value = clean_text(value)

    if not value or key in specifications:
        return False

    specifications[key] = {
        "value": value,
        "label": label,
        "source": "shopify_oxygen_stream",
        "confidence": confidence,
    }

    return True


def extract_shopify_oxygen_specs(
    html: str,
    specifications: dict[str, dict[str, Any]],
) -> int:
    """
    Extract high-confidence specifications from Shopify Hydrogen/Oxygen
    React Router stream data. This is intentionally conservative.
    """

    text = decode_shopify_oxygen_stream(html)

    if not text:
        return 0

    extracted = 0

    patterns: list[tuple[str, str, str, int]] = [
        (
            "processor",
            "Processor",
            r"\b(?:Qualcomm\s+)?Snapdragon\s+[0-9A-Za-z+\- ]{2,40}?(?=\\|\"|,|\[|\{|\.|mobile platform)",
            88,
        ),
        (
            "memory_type",
            "Memory type",
            r"\bLPDDR(?:4X|5|5X)\b",
            86,
        ),
        (
            "storage_type",
            "Storage type",
            r"\bUFS\s*\d+(?:\.\d+)?\b",
            86,
        ),
        (
            "display_size_refresh",
            "Display",
            r"\b\d+(?:\.\d+)?\\?\"\s*(?:flexible\s+)?AMOLED\s+display\b",
            86,
        ),
        (
            "refresh_rate",
            "Refresh rate",
            r"\b(?:up to\s+)?\d{2,3}\s*Hz\b",
            82,
        ),
        (
            "peak_brightness",
            "Peak brightness",
            r"\b\d{3,5}\s*nits\b",
            82,
        ),
        (
            "pixel_density",
            "Pixel density",
            r"\b\d{3,4}\s*ppi\b",
            82,
        ),
        (
            "battery_capacity",
            "Battery capacity",
            r"\b\d{4,5}\s*mAh\b",
            88,
        ),
        (
            "wired_charging",
            "Wired charging",
            r"\b\d{2,3}\s*W\s*fast charging\b",
            86,
        ),
        (
            "wireless_charging",
            "Wireless charging",
            r"\b\d{1,3}\s*W\s*wireless charging\b",
            84,
        ),
        (
            "reverse_wireless_charging",
            "Reverse wireless charging",
            r"\b\d{1,3}\s*W\s*reverse wireless charging\b",
            84,
        ),
        (
            "reverse_wired_charging",
            "Reverse wired charging",
            r"\b\d{1,3}(?:\.\d+)?\s*W\s*reverse wired charging\b",
            84,
        ),
        (
            "ip_rating",
            "Ingress protection",
            r"\bIP\d{2}\b",
            88,
        ),
        (
            "operating_system",
            "Operating system",
            r"\bNothing OS\s*\d+(?:\.\d+)?\s*(?:powered by|based on)?\s*Android\s*\d+\b",
            86,
        ),
        (
            "android_updates",
            "Android updates",
            r"\b\d+\s+years?\s+of\s+Android updates\b",
            82,
        ),
        (
            "security_updates",
            "Security updates",
            r"\b\d+\s+years?\s+of\s+security (?:patches|updates)\b",
            82,
        ),
        (
            "bluetooth",
            "Bluetooth",
            r"\bBluetooth\s*\d+(?:\.\d+)?\b",
            80,
        ),
        (
            "wifi",
            "Wi-Fi",
            r"\bWi-?Fi\s*\d\b",
            80,
        ),
    ]

    for key, label, pattern, confidence in patterns:
        match = re.search(pattern, text, flags=re.I)

        if not match:
            continue

        value = match.group(0).strip(" ,.;:-")

        if add_stream_spec(
            specifications,
            key,
            label,
            value,
            confidence,
        ):
            extracted += 1

    return extracted


def page_identity_score(
    expected_name: str,
    page_title: str,
    canonical_url: str,
) -> float:
    expected = identity_tokens(expected_name)

    if not expected:
        return 0.0

    title_tokens = identity_tokens(page_title)
    url_tokens = identity_tokens(
        canonical_url.replace("-", " ").replace("/", " ")
    )
    combined_page_tokens = title_tokens.union(url_tokens)

    title_score = len(expected.intersection(title_tokens)) / len(expected)
    url_score = len(expected.intersection(url_tokens)) / len(expected)
    score = (title_score * 0.7) + (url_score * 0.3)

    # Numeric model suffixes are identity-bearing:
    # "Buds Air 8" must not be accepted as "Buds Air".
    expected_numeric = {token for token in expected if token.isdigit()}
    missing_numeric = expected_numeric.difference(combined_page_tokens)

    if missing_numeric:
        score = min(score, 0.49)

    return round(score, 4)


def extract_one(
    research_result: dict[str, Any],
    identity: dict[str, Any],
) -> dict[str, Any]:
    product_id = str(research_result.get("product_id") or "")
    official_url = clean_text(research_result.get("official_url"))
    expected_name = clean_text(
        research_result.get("core_title")
        or identity.get("search_name")
        or research_result.get("title")
    )

    output: dict[str, Any] = {
        "product_id": product_id,
        "brand": clean_text(
            identity.get("brand")
            or research_result.get("brand")
        ),
        "model": clean_text(identity.get("model")),
        "search_name": expected_name,
        "official_url": official_url,
        "source_host": hostname(official_url),
        "resolver_status": research_result.get("status"),
        "resolver_verified": research_result.get("verified") is True,
        "fetch_status": "pending",
        "http_status": None,
        "page_identity_score": 0.0,
        "specifications": {},
        "features": [],
        "meta": {},
        "evidence_summary": {},
        "review": {
            "approved": False,
            "status": "manual_review",
            "reason": "",
        },
        "extracted_at": utc_now(),
    }

    if not official_url:
        output["fetch_status"] = "skipped"
        output["review"]["reason"] = "No official URL available"
        return output

    if is_unwanted_url(official_url):
        output["fetch_status"] = "rejected"
        output["review"]["reason"] = "URL matches an excluded page type"
        return output

    html, error, status_code = fetch_page(official_url)
    output["http_status"] = status_code

    if html is None:
        output["fetch_status"] = "error"
        output["review"]["reason"] = error or "Unable to fetch page"
        return output

    try:
        soup = BeautifulSoup(html, "lxml")
        parser_name = "lxml"
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        parser_name = "html.parser"

    json_ld_products = parse_json_ld(soup)
    meta = extract_meta(soup)

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    remove_page_chrome(soup)

    specifications: dict[str, dict[str, Any]] = {}
    json_ld_count = extract_json_ld_specs(json_ld_products, specifications)
    table_count = extract_tables(soup, specifications)
    definition_count = extract_definition_lists(soup, specifications)
    block_count = extract_label_value_blocks(soup, specifications)
    shopify_oxygen_count = extract_shopify_oxygen_specs(
        html,
        specifications,
    )

    if len(specifications) > MAX_SPECS:
        specifications = dict(list(specifications.items())[:MAX_SPECS])

    features = extract_features(soup)
    page_title = (
        meta.get("html_title")
        or meta.get("og_title")
        or meta.get("h1")
        or ""
    )
    canonical_url = meta.get("canonical_url") or official_url
    match_score = page_identity_score(
        expected_name,
        page_title,
        canonical_url,
    )

    output["fetch_status"] = "success"
    output["page_identity_score"] = match_score
    output["specifications"] = specifications
    output["features"] = features
    output["meta"] = meta
    output["evidence_summary"] = {
        "parser": parser_name,
        "json_ld_products": len(json_ld_products),
        "json_ld_specifications": json_ld_count,
        "table_specifications": table_count,
        "definition_list_specifications": definition_count,
        "label_value_specifications": block_count,
        "shopify_oxygen_specifications": shopify_oxygen_count,
        "total_specifications": len(specifications),
        "feature_items": len(features),
        "noise_filter_version": "2.0",
    }

    evidence_count = len(specifications) + len(features)

    if (
        output["resolver_verified"] is True
        and match_score >= 0.80
        and evidence_count >= 3
    ):
        output["review"]["status"] = "candidate_ready"
        output["review"]["reason"] = (
            "Page identity and extracted evidence are strong enough for review"
        )
    elif match_score >= 0.50 and evidence_count >= 1:
        output["review"]["status"] = "manual_review"
        output["review"]["reason"] = (
            "Evidence was extracted, but page identity requires review"
        )
    else:
        output["review"]["status"] = "rejected_candidate"
        output["review"]["reason"] = (
            "Page does not match the expected product strongly enough"
        )

    return output


def load_existing_output() -> dict[str, dict[str, Any]]:
    payload = load_json(OUTPUT_DB, {"products": []})

    products = (
        payload.get("products", [])
        if isinstance(payload, dict)
        else []
    )

    if not isinstance(products, list):
        return {}

    return {
        str(item.get("product_id")): item
        for item in products
        if isinstance(item, dict)
        and item.get("product_id") not in (None, "")
    }


def backup_output() -> Path | None:
    if not OUTPUT_DB.exists():
        return None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = OUTPUT_DB.with_name(
        f"{OUTPUT_DB.stem}_before_incremental_{stamp}{OUTPUT_DB.suffix}"
    )

    shutil.copy2(OUTPUT_DB, destination)
    return destination


def select_research_results(
    products: list[dict[str, Any]],
    existing: dict[str, dict[str, Any]],
    only_verified: bool,
    pending: bool,
    product_ids: list[str],
    limit: int | None,
) -> list[dict[str, Any]]:
    requested_ids = {
        str(product_id).strip()
        for product_id in product_ids
        if str(product_id).strip()
    }

    selected: list[dict[str, Any]] = []

    for product in products:
        if not isinstance(product, dict):
            continue

        product_id = str(product.get("product_id") or "").strip()

        if not product.get("official_url"):
            continue

        if only_verified and product.get("verified") is not True:
            continue

        if requested_ids:
            if product_id not in requested_ids:
                continue
        elif pending:
            if product_id in existing:
                continue

        selected.append(product)

    if limit is not None and limit >= 0:
        selected = selected[:limit]

    return selected


def build_output(
    limit: int | None,
    only_verified: bool,
    pending: bool = False,
    product_ids: list[str] | None = None,
) -> dict[str, Any]:
    research_payload = load_json(
        RESEARCH_RESULTS_DB,
        {"products": []},
    )
    identity_index = load_identity_index()
    existing = load_existing_output()

    products = (
        research_payload.get("products", [])
        if isinstance(research_payload, dict)
        else []
    )

    if not isinstance(products, list):
        raise ValueError("research_results.json products must be a list")

    selected = select_research_results(
        products=products,
        existing=existing,
        only_verified=only_verified,
        pending=pending,
        product_ids=product_ids or [],
        limit=limit,
    )

    updated = dict(existing)
    processed_results: list[dict[str, Any]] = []

    for position, research_result in enumerate(selected, start=1):
        product_id = str(research_result.get("product_id") or "")
        identity = identity_index.get(product_id, {})

        print("\n" + "=" * 68)
        print(
            f"[{position}/{len(selected)}] Extracting:",
            identity.get("search_name")
            or research_result.get("title"),
        )
        print("URL:", research_result.get("official_url"))

        try:
            result = extract_one(research_result, identity)
        except Exception as error:
            result = {
                "product_id": product_id,
                "official_url": research_result.get("official_url"),
                "resolver_status": research_result.get("status"),
                "resolver_verified": research_result.get("verified") is True,
                "fetch_status": "error",
                "http_status": None,
                "page_identity_score": 0.0,
                "specifications": {},
                "features": [],
                "meta": {},
                "evidence_summary": {},
                "review": {
                    "approved": False,
                    "status": "manual_review",
                    "reason": str(error),
                },
                "extracted_at": utc_now(),
            }

        updated[product_id] = result
        processed_results.append(result)

        print("Fetch status :", result.get("fetch_status"))
        print("Page match   :", result.get("page_identity_score"))
        print(
            "Specs found  :",
            result.get("evidence_summary", {}).get(
                "total_specifications",
                0,
            ),
        )
        print(
            "Review status:",
            result.get("review", {}).get("status"),
        )

        time.sleep(DELAY_SECONDS)

    final_products = list(updated.values())

    batch_summary = {
        "requested": len(selected),
        "success": sum(
            1 for item in processed_results
            if item.get("fetch_status") == "success"
        ),
        "errors": sum(
            1 for item in processed_results
            if item.get("fetch_status") == "error"
        ),
        "candidate_ready": sum(
            1 for item in processed_results
            if item.get("review", {}).get("status") == "candidate_ready"
        ),
        "manual_review": sum(
            1 for item in processed_results
            if item.get("review", {}).get("status") == "manual_review"
        ),
        "rejected_candidate": sum(
            1 for item in processed_results
            if item.get("review", {}).get("status") == "rejected_candidate"
        ),
    }

    total_summary = {
        "products": len(final_products),
        "successful_fetch": sum(
            1 for item in final_products
            if item.get("fetch_status") == "success"
        ),
        "candidate_ready": sum(
            1 for item in final_products
            if item.get("review", {}).get("status") == "candidate_ready"
        ),
        "manual_review": sum(
            1 for item in final_products
            if item.get("review", {}).get("status") == "manual_review"
        ),
        "rejected_candidate": sum(
            1 for item in final_products
            if item.get("review", {}).get("status") == "rejected_candidate"
        ),
    }

    return {
        "schema_version": "5.0",
        "generated_at": utc_now(),
        "source_file": str(RESEARCH_RESULTS_DB.relative_to(ROOT)),
        "mode": "incremental",
        "selection": {
            "only_verified": only_verified,
            "pending": pending,
            "product_ids": product_ids or [],
            "limit": limit,
        },
        "batch_summary": batch_summary,
        "summary": total_summary,
        "products": final_products,
    }


def print_status() -> int:
    output_payload = load_json(OUTPUT_DB, {"products": []})
    research_payload = load_json(
        RESEARCH_RESULTS_DB,
        {"products": []},
    )

    output_products = (
        output_payload.get("products", [])
        if isinstance(output_payload, dict)
        else []
    )
    research_products = (
        research_payload.get("products", [])
        if isinstance(research_payload, dict)
        else []
    )

    if not isinstance(output_products, list):
        output_products = []

    if not isinstance(research_products, list):
        research_products = []

    extracted_ids = {
        str(item.get("product_id"))
        for item in output_products
        if isinstance(item, dict)
        and item.get("product_id") not in (None, "")
    }

    verified_eligible = [
        item
        for item in research_products
        if isinstance(item, dict)
        and item.get("official_url")
        and item.get("verified") is True
    ]

    all_url_candidates = [
        item
        for item in research_products
        if isinstance(item, dict)
        and item.get("official_url")
    ]

    pending_verified = sum(
        1
        for item in verified_eligible
        if str(item.get("product_id")) not in extracted_ids
    )

    print("\n" + "=" * 68)
    print("OFFICIAL SPECIFICATION EXTRACTOR v5.0 - STATUS")
    print("=" * 68)
    print("Research results        :", len(research_products))
    print("Official URL candidates :", len(all_url_candidates))
    print("Verified eligible       :", len(verified_eligible))
    print("Extracted products      :", len(output_products))
    print("Pending verified        :", pending_verified)
    print(
        "Successful fetch        :",
        sum(
            1 for item in output_products
            if item.get("fetch_status") == "success"
        ),
    )
    print(
        "Candidate ready         :",
        sum(
            1 for item in output_products
            if item.get("review", {}).get("status") == "candidate_ready"
        ),
    )
    print(
        "Manual review           :",
        sum(
            1 for item in output_products
            if item.get("review", {}).get("status") == "manual_review"
        ),
    )
    print(
        "Rejected candidate      :",
        sum(
            1 for item in output_products
            if item.get("review", {}).get("status") == "rejected_candidate"
        ),
    )
    print("=" * 68)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract review-ready product specifications from official pages"
        )
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=("extract", "status"),
        default="status",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of selected products to process",
    )

    parser.add_argument(
        "--all-candidates",
        action="store_true",
        help=(
            "Include manual-review resolver results. "
            "Default processes resolver-verified products only."
        ),
    )

    parser.add_argument(
        "--pending",
        action="store_true",
        help="Process only eligible products not already extracted",
    )

    parser.add_argument(
        "--product-id",
        action="append",
        default=[],
        help="Extract a specific product ID; may be repeated",
    )

    args = parser.parse_args()

    if args.command == "status":
        return print_status()

    try:
        output = build_output(
            limit=args.limit,
            only_verified=not args.all_candidates,
            pending=args.pending,
            product_ids=args.product_id,
        )

        backup = backup_output()
        save_json(OUTPUT_DB, output)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    summary = output["batch_summary"]

    print("\n" + "=" * 68)
    print("COUPON WORLD OFFICIAL SPECIFICATION EXTRACTOR v5.0")
    print("=" * 68)
    print("Requested         :", summary["requested"])
    print("Successful fetch  :", summary["success"])
    print("Candidate ready   :", summary["candidate_ready"])
    print("Manual review     :", summary["manual_review"])
    print("Rejected candidate:", summary["rejected_candidate"])
    print("Errors            :", summary["errors"])
    print("Total stored      :", len(output.get("products", [])))
    print("Backup            :", backup)
    print("Output            :", OUTPUT_DB)
    print("=" * 68)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
