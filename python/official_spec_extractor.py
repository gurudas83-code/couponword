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
    key = re.sub(r"[:ï¼š]+$", "", key)
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
                r"^([A-Za-z][A-Za-z0-9 /+&()._-]{1,55})\s*[:ï¼š]\s*(.{2,300})$",
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





def extract_structured_sections(
    soup: BeautifulSoup,
    specifications: dict[str, dict[str, Any]],
) -> int:
    """
    Extract specifications from generic heading/content sections.

    This reader is brand-agnostic. It looks for technical headings inside
    section-like containers and stores nearby content through the common
    add_specification() path.
    """

    before = len(specifications)
    seen_pairs: set[tuple[str, str]] = set()

    heading_selectors = (
        "h2",
        "h3",
        "h4",
        "[role='heading']",
        "summary",
    )

    technical_container_hints = (
        "spec",
        "tech",
        "detail",
        "feature",
        "attribute",
        "accordion",
        "product-info",
        "product_info",
        "characteristic",
        "configuration",
    )

    for heading in soup.select(", ".join(heading_selectors)):
        raw_label = clean_text(heading.get_text(" ", strip=True))

        if not raw_label:
            continue

        if len(raw_label) < 2 or len(raw_label) > 90:
            continue

        if is_noise_feature(raw_label):
            continue

        container = heading.find_parent(["section", "article", "li"])

        if container is None:
            parent = heading.parent

            while parent is not None and parent.name not in {"body", "html"}:
                class_text = " ".join(parent.get("class", []))
                id_text = str(parent.get("id") or "")
                signature = f"{class_text} {id_text}".lower()

                if any(
                    hint in signature
                    for hint in technical_container_hints
                ):
                    container = parent
                    break

                parent = parent.parent

        if container is None:
            container = heading.parent

        if container is None:
            continue

        container_copy = BeautifulSoup(str(container), "lxml")
        copied_heading = container_copy.select_one(
            ", ".join(heading_selectors)
        )

        if copied_heading is not None:
            copied_heading.decompose()

        for node in container_copy.select(
            "script, style, noscript, svg, img, button, nav, footer, "
            "[class*='price'], [class*='buy'], [class*='cart']"
        ):
            node.decompose()

        value = clean_text(
            container_copy.get_text(" ", strip=True)
        )

        if not value:
            continue

        if len(value) < 2 or len(value) > 500:
            continue

        if is_noise_feature(value):
            continue

        normalized_label = normalize_key(raw_label)

        label_is_known = (
            normalized_label in set(ALIASES.values())
            or clean_text(raw_label).lower() in ALIASES
        )

        combined_text = f"{raw_label} {value}".lower()
        relevance = sum(
            1
            for hint in FEATURE_HINTS
            if hint in combined_text
        )

        if not label_is_known and relevance <= 0:
            continue

        pair = (
            clean_text(raw_label).lower(),
            clean_text(value).lower(),
        )

        if pair in seen_pairs:
            continue

        seen_pairs.add(pair)

        confidence = min(
            92,
            82 + min(10, relevance * 2),
        )

        add_specification(
            specifications,
            raw_label,
            value,
            "structured_section",
            confidence,
        )

    return len(specifications) - before


def extract_apple_techspecs(
    soup: BeautifulSoup,
    specifications: dict[str, dict[str, Any]],
    official_url: str,
) -> int:
    """
    Extract structured specifications from Apple technical-specification
    pages that use techspecs-row / techspecs-rowheader markup.
    """

    if "apple.com" not in str(official_url or "").lower():
        return 0

    rows = soup.select(".techspecs-row")

    if not rows:
        return 0

    before = len(specifications)

    section_key_map = {
        "finish": ("finish", "Finish"),
        "capacity": ("storage_capacity", "Storage capacity"),
        "size and weight": ("size_and_weight", "Size and weight"),
        "display": ("display", "Display"),
        "splash water and dust resistant": (
            "ip_rating",
            "Splash, water and dust resistance",
        ),
        "splash water and dust resistance": (
            "ip_rating",
            "Splash, water and dust resistance",
        ),
        "chip": ("processor", "Processor"),
        "camera": ("camera", "Camera"),
        "true depth camera": ("front_camera", "Front camera"),
        "truedepth camera": ("front_camera", "Front camera"),
        "video recording": ("video_recording", "Video recording"),
        "power and battery": ("battery", "Power and battery"),
        "charging and expansion": (
            "charging_and_connector",
            "Charging and connector",
        ),
        "external buttons and connectors": (
            "external_connectors",
            "External buttons and connectors",
        ),
        "cellular and wireless": (
            "connectivity",
            "Cellular and wireless",
        ),
        "sim card": ("sim", "SIM"),
        "operating system": ("operating_system", "Operating system"),
        "audio playback": ("audio", "Audio playback"),
        "video playback": ("video_playback", "Video playback"),
        "accessibility": ("accessibility", "Accessibility"),
        "environmental requirements": (
            "environmental_requirements",
            "Environmental requirements",
        ),
    }

    for row in rows:
        header = row.select_one(".techspecs-rowheader")

        if header is None:
            continue

        raw_label = clean_text(header.get_text(" ", strip=True))

        if not raw_label:
            continue

        label_without_footnote = re.sub(
            r"\s+\d+\s*$",
            "",
            raw_label,
        ).strip()

        normalized_label = re.sub(
            r"[^a-z0-9]+",
            " ",
            label_without_footnote.lower(),
        ).strip()

        row_copy = BeautifulSoup(str(row), "lxml")
        copied_header = row_copy.select_one(".techspecs-rowheader")

        if copied_header is not None:
            copied_header.decompose()

        value = clean_text(
            row_copy.get_text(" ", strip=True)
        )

        if not value or len(value) < 2:
            continue

        key, label = section_key_map.get(
            normalized_label,
            (
                re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    normalized_label,
                ).strip("_"),
                label_without_footnote,
            ),
        )

        if not key:
            continue

        add_specification(
            specifications,
            label,
            value,
            "apple_techspecs",
            94,
        )

        lowered_value = value.lower()

        if "ip68" in lowered_value:
            add_specification(
                specifications,
                "Ingress protection",
                "IP68",
                "apple_techspecs",
                96,
            )

        chip_match = re.search(
            r"\bA\d{1,2}(?:\s+Pro)?\s+chip\b",
            value,
            flags=re.I,
        )

        if chip_match:
            add_specification(
                specifications,
                "Processor",
                clean_text(chip_match.group(0)),
                "apple_techspecs",
                96,
            )

        display_match = re.search(
            r"\b\d+(?:\.\d+)?[â€‘-]inch[^.]{0,180}?"
            r"(?:OLED|LCD)\s+display\b",
            value,
            flags=re.I,
        )

        if display_match:
            add_specification(
                specifications,
                "Display",
                clean_text(display_match.group(0)),
                "apple_techspecs",
                95,
            )

        camera_match = re.search(
            r"\b\d{1,3}MP[^.]{0,120}?"
            r"(?:camera system|camera)\b",
            value,
            flags=re.I,
        )

        if camera_match:
            add_specification(
                specifications,
                "Main camera",
                clean_text(camera_match.group(0)),
                "apple_techspecs",
                95,
            )

        battery_match = re.search(
            r"Video playback\s+Up to\s+\d+\s+hours",
            value,
            flags=re.I,
        )

        if battery_match:
            add_specification(
                specifications,
                "Video playback",
                clean_text(battery_match.group(0)),
                "apple_techspecs",
                94,
            )

        fast_charge_match = re.search(
            r"Up to\s+50%\s+charge\s+in\s+\d+\s+minutes",
            value,
            flags=re.I,
        )

        if fast_charge_match:
            add_specification(
                specifications,
                "Fast charging",
                clean_text(fast_charge_match.group(0)),
                "apple_techspecs",
                94,
            )

        storage_values = re.findall(
            r"\b(?:128|256|512)GB\b|\b[12]TB\b",
            value,
            flags=re.I,
        )

        if normalized_label == "capacity" and storage_values:
            add_specification(
                specifications,
                "Storage options",
                ", ".join(dict.fromkeys(storage_values)),
                "apple_techspecs",
                95,
            )

    return len(specifications) - before


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



EMBEDDED_STATE_KEY_HINTS = (
    "spec",
    "specification",
    "processor",
    "chip",
    "cpu",
    "gpu",
    "memory",
    "ram",
    "storage",
    "capacity",
    "display",
    "screen",
    "resolution",
    "refresh",
    "brightness",
    "camera",
    "battery",
    "charging",
    "bluetooth",
    "wifi",
    "wireless",
    "connectivity",
    "driver",
    "microphone",
    "latency",
    "codec",
    "audio",
    "water",
    "dust",
    "ip",
    "weight",
    "height",
    "width",
    "depth",
    "dimension",
    "operating system",
    "os",
    "material",
    "color",
    "colour",
)

EMBEDDED_STATE_VALUE_HINTS = (
    "mah",
    "hz",
    "khz",
    "mp",
    "gb",
    "tb",
    "w ",
    " watt",
    "bluetooth",
    "wi-fi",
    "wifi",
    "ip5",
    "ip6",
    "ipx",
    "oled",
    "amoled",
    "lcd",
    "snapdragon",
    "mediatek",
    "dimensity",
    "android",
    "ios",
    "playback",
    "charging",
    "noise cancellation",
    "anc",
    "enc",
    "driver",
    "latency",
    "codec",
    "mm",
    "grams",
    " gram",
)


def decode_indexed_state_graph(payload: Any) -> Any:
    """
    Decode reference-indexed application-state payloads conservatively.
    """

    if not isinstance(payload, list) or not payload:
        return payload

    looks_indexed = (
        payload[0] == "Reactive"
        or any(
            isinstance(item, dict)
            and any(
                isinstance(value, int)
                and 0 <= value < len(payload)
                for value in item.values()
            )
            for item in payload[:8]
        )
    )

    if not looks_indexed:
        return payload

    def decode(
        value: Any,
        depth: int = 0,
        seen: set[int] | None = None,
    ) -> Any:
        if seen is None:
            seen = set()

        if depth > 30:
            return None

        if isinstance(value, int):
            if value < 0 or value >= len(payload):
                return value

            if value in seen:
                return None

            next_seen = set(seen)
            next_seen.add(value)

            return decode(
                payload[value],
                depth + 1,
                next_seen,
            )

        if isinstance(value, list):
            return [
                decode(item, depth + 1, seen)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(key): decode(item, depth + 1, seen)
                for key, item in value.items()
            }

        return value

    return decode(0)


def embedded_value_is_useful(key: str, value: str) -> bool:
    key_text = clean_text(key).lower()
    value_text = clean_text(value).lower()

    if not key_text or not value_text:
        return False

    if len(value_text) < 2 or len(value_text) > 500:
        return False

    # Reject common hydration sentinels / internal state markers.
    if value_text in {
        "-1",
        "0",
        "1",
        "true",
        "false",
        "none",
        "null",
        "undefined",
    }:
        return False

    if value_text.startswith(
        ("http://", "https://", "data:image/", "<ref:")
    ):
        return False

    if is_noise_feature(f"{key_text} {value_text}"):
        return False

    # Token-aware key matching prevents short hints such as "os"
    # from matching unrelated keys such as "svideos".
    key_tokens = set(
        re.findall(r"[a-z0-9]+", key_text)
    )

    normalized_key = re.sub(
        r"[^a-z0-9]+",
        " ",
        key_text,
    ).strip()

    key_match = False

    for hint in EMBEDDED_STATE_KEY_HINTS:
        normalized_hint = re.sub(
            r"[^a-z0-9]+",
            " ",
            hint.lower(),
        ).strip()

        hint_tokens = set(normalized_hint.split())

        if not hint_tokens:
            continue

        if len(hint_tokens) == 1:
            token = next(iter(hint_tokens))

            if token in key_tokens:
                key_match = True
                break
        elif normalized_hint in normalized_key:
            key_match = True
            break

    if not key_match:
        return False

    value_match = any(
        hint in value_text
        for hint in EMBEDDED_STATE_VALUE_HINTS
    )

    numeric_value = bool(
        re.search(
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:mah|hz|khz|mp|gb|tb|w|mm|cm|g|kg|hours?|hrs?|ms|db)\b",
            value_text,
            flags=re.I,
        )
    )

    return value_match or numeric_value


def extract_embedded_state_specs(
    html: str,
    specifications: dict[str, dict[str, Any]],
) -> int:
    """
    Extract conservative specification evidence from embedded application
    state such as application/json, Next.js data, Nuxt data and hydration
    payloads.
    """

    before = len(specifications)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    payloads: list[tuple[str, Any]] = []

    for script in soup.find_all("script"):
        script_type = str(script.get("type") or "").lower()
        script_id = str(script.get("id") or "")
        raw = script.string or script.get_text("", strip=False)

        if not raw:
            continue

        is_json_script = (
            "application/json" in script_type
            or script_id in {
                "__NEXT_DATA__",
                "__NUXT_DATA__",
            }
        )

        if not is_json_script:
            continue

        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        decoded = decode_indexed_state_graph(payload)

        source_name = "embedded_application_state"

        if script_id == "__NEXT_DATA__":
            source_name = "embedded_next_state"
        elif script_id == "__NUXT_DATA__":
            source_name = "embedded_indexed_state"

        payloads.append((source_name, decoded))

    seen_pairs: set[tuple[str, str]] = set()

    def walk(
        value: Any,
        source_name: str,
        depth: int = 0,
    ) -> None:
        if depth > 20:
            return

        if isinstance(value, dict):
            for key, item in value.items():
                key_text = clean_text(key)

                if isinstance(item, (str, int, float, bool)):
                    item_text = clean_text(item)

                    if embedded_value_is_useful(
                        key_text,
                        item_text,
                    ):
                        pair = (
                            key_text.lower(),
                            item_text.lower(),
                        )

                        if pair not in seen_pairs:
                            seen_pairs.add(pair)

                            confidence = 86

                            if any(
                                token in key_text.lower()
                                for token in (
                                    "spec",
                                    "processor",
                                    "battery",
                                    "display",
                                    "camera",
                                    "bluetooth",
                                    "charging",
                                    "driver",
                                    "ip",
                                )
                            ):
                                confidence = 90

                            add_specification(
                                specifications,
                                key_text,
                                item_text,
                                source_name,
                                confidence,
                            )

                walk(
                    item,
                    source_name,
                    depth + 1,
                )

        elif isinstance(value, list):
            for item in value:
                walk(
                    item,
                    source_name,
                    depth + 1,
                )

    for source_name, payload in payloads:
        walk(
            payload,
            source_name,
        )

    return len(specifications) - before


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



def collect_official_source_urls(
    research_result: dict[str, Any],
) -> list[dict[str, str]]:
    """Collect unique official source candidates in resolver-ranked order."""

    collected: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(url: Any, source_type: Any = "official_page") -> None:
        clean_url = clean_text(url)

        if not clean_url or clean_url in seen:
            return

        seen.add(clean_url)
        collected.append(
            {
                "url": clean_url,
                "source_type": clean_text(source_type) or "official_page",
            }
        )

    add(
        research_result.get("official_url"),
        research_result.get("primary_source_type") or "primary",
    )

    for candidate in research_result.get("candidates", []):
        if not isinstance(candidate, dict):
            continue

        add(
            candidate.get("url"),
            candidate.get("source_type"),
        )

    source_groups = research_result.get("source_candidates", {})

    if isinstance(source_groups, dict):
        for source_type, candidates in source_groups.items():
            if not isinstance(candidates, list):
                continue

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue

                add(
                    candidate.get("url"),
                    candidate.get("source_type") or source_type,
                )

    return collected


def merge_evidence_records(
    base: dict[str, Any],
    extra: dict[str, Any],
) -> dict[str, Any]:
    """Merge a second official-source extraction into the primary result."""

    base_specs = base.setdefault("specifications", {})
    extra_specs = extra.get("specifications", {})

    if isinstance(base_specs, dict) and isinstance(extra_specs, dict):
        for key, record in extra_specs.items():
            if not isinstance(record, dict):
                continue

            existing = base_specs.get(key)
            incoming_confidence = int(record.get("confidence") or 0)
            existing_confidence = (
                int(existing.get("confidence") or 0)
                if isinstance(existing, dict)
                else -1
            )

            if existing is None or incoming_confidence > existing_confidence:
                merged_record = dict(record)
                merged_record["source_url"] = extra.get("official_url")
                base_specs[key] = merged_record

    base_features = base.setdefault("features", [])
    extra_features = extra.get("features", [])

    if isinstance(base_features, list) and isinstance(extra_features, list):
        seen_features = {
            clean_text(item.get("text")).lower()
            for item in base_features
            if isinstance(item, dict) and clean_text(item.get("text"))
        }

        for item in extra_features:
            if not isinstance(item, dict):
                continue

            text = clean_text(item.get("text"))
            lowered = text.lower()

            if not text or lowered in seen_features:
                continue

            merged_item = dict(item)
            merged_item["source_url"] = extra.get("official_url")
            base_features.append(merged_item)
            seen_features.add(lowered)

    return base


def apply_review_decision(
    output: dict[str, Any],
) -> None:
    """Apply the standard review decision after evidence has been merged."""

    specifications = output.get("specifications", {})
    features = output.get("features", [])
    summary = output.get("evidence_summary", {})

    evidence_count = (
        len(specifications) if isinstance(specifications, dict) else 0
    ) + (
        len(features) if isinstance(features, list) else 0
    )

    match_score = float(output.get("page_identity_score") or 0)
    structured_count = int(
        summary.get("structured_section_specifications") or 0
    )
    apple_count = int(
        summary.get("apple_techspecs_specifications") or 0
    )

    if (
        output.get("resolver_verified") is True
        and (
            match_score >= 0.80
            or (
                structured_count + apple_count >= 5
                and match_score >= 0.70
            )
        )
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



MEDIA_IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)


def collect_embedded_media_evidence(
    html: str,
) -> dict[str, Any]:
    """
    Collect image evidence from embedded application state.

    This is intentionally evidence-only: image URLs are never promoted
    directly into verified specifications.
    """

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    payloads: list[Any] = []

    for script in soup.find_all("script"):
        script_type = str(script.get("type") or "").lower()
        script_id = str(script.get("id") or "")
        raw = script.string or script.get_text("", strip=False)

        if not raw:
            continue

        if not (
            "application/json" in script_type
            or script_id in {
                "__NEXT_DATA__",
                "__NUXT_DATA__",
            }
        ):
            continue

        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        payloads.append(
            decode_indexed_state_graph(payload)
        )

    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def classify_path(path: str) -> str:
        lowered = path.lower()

        if any(
            token in lowered
            for token in (
                ".icon",
                ".icons",
                ".logo",
                ".logos",
                ".avatar",
                ".badge",
                ".dialog",
                ".navbar",
                ".footer",
            )
        ):
            return "ui_asset"

        if any(
            token in lowered
            for token in (
                ".mobile",
                "[mobile]",
                "_mobile",
            )
        ):
            return "product_mobile"

        if any(
            token in lowered
            for token in (
                ".desktop",
                "[desktop]",
                ".pc",
                "[pc]",
            )
        ):
            return "product_desktop"

        return "product_candidate"

    def walk(
        value: Any,
        path: str = "root",
        depth: int = 0,
    ) -> None:
        if depth > 25:
            return

        if isinstance(value, dict):
            for key, item in value.items():
                walk(
                    item,
                    f"{path}.{key}",
                    depth + 1,
                )

        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(
                    item,
                    f"{path}[{index}]",
                    depth + 1,
                )

        elif isinstance(value, str):
            url = value.strip()

            if not url.lower().startswith(
                ("http://", "https://")
            ):
                return

            try:
                parsed_path = urlparse(url).path.lower()
            except ValueError:
                return

            if not parsed_path.endswith(
                MEDIA_IMAGE_EXTENSIONS
            ):
                return

            if url in seen_urls:
                return

            seen_urls.add(url)

            items.append(
                {
                    "url": url,
                    "path": path,
                    "role": classify_path(path),
                }
            )

    for payload in payloads:
        walk(payload)

    product_items = [
        item
        for item in items
        if item.get("role") != "ui_asset"
    ]

    ui_items = [
        item
        for item in items
        if item.get("role") == "ui_asset"
    ]

    desktop_count = sum(
        1
        for item in product_items
        if item.get("role") == "product_desktop"
    )

    mobile_count = sum(
        1
        for item in product_items
        if item.get("role") == "product_mobile"
    )

    generic_count = sum(
        1
        for item in product_items
        if item.get("role") == "product_candidate"
    )

    return {
        "collector": "embedded_application_state",
        "total_images": len(items),
        "product_image_count": len(product_items),
        "desktop_count": desktop_count,
        "mobile_count": mobile_count,
        "generic_candidate_count": generic_count,
        "excluded_ui_assets": len(ui_items),
        "product_images": product_items[:80],
        "ui_assets": ui_items[:30],
        "ocr_status": "not_run",
        "vision_status": "not_run",
    }



def rank_media_evidence(
    media_evidence: dict[str, Any],
    max_scan: int = 20,
    top_n: int = 8,
) -> dict[str, Any]:
    """
    Rank product-image evidence for later vision/OCR review.

    This function is evidence-only. It does not publish, copy, or promote
    image content into verified specifications.
    """

    if not isinstance(media_evidence, dict):
        return media_evidence

    product_images = media_evidence.get("product_images", [])

    if not isinstance(product_images, list) or not product_images:
        media_evidence["ranker_status"] = "no_images"
        media_evidence["vision_candidates"] = []
        return media_evidence

    try:
        from io import BytesIO
        from PIL import Image, ImageFilter, ImageStat
    except ImportError:
        media_evidence["ranker_status"] = "dependency_missing"
        media_evidence["ranker_reason"] = "Pillow is not installed"
        media_evidence["vision_candidates"] = []
        return media_evidence

    desktop = [
        item
        for item in product_images
        if isinstance(item, dict)
        and item.get("role") == "product_desktop"
    ]

    mobile = [
        item
        for item in product_images
        if isinstance(item, dict)
        and item.get("role") == "product_mobile"
    ]

    generic = [
        item
        for item in product_images
        if isinstance(item, dict)
        and item.get("role") == "product_candidate"
    ]

    scan_items = (
        desktop
        if desktop
        else mobile
        if mobile
        else generic
    )[:max_scan]

    def dhash(image: Any, hash_size: int = 8) -> int:
        gray = image.convert("L").resize(
            (hash_size + 1, hash_size)
        )

        pixels = list(gray.get_flattened_data())

        bits: list[bool] = []

        for row in range(hash_size):
            start = row * (hash_size + 1)

            for col in range(hash_size):
                bits.append(
                    pixels[start + col]
                    > pixels[start + col + 1]
                )

        value = 0

        for bit in bits:
            value = (value << 1) | int(bit)

        return value

    def complexity(image: Any) -> tuple[float, float]:
        sample = image.convert("L")
        sample.thumbnail((600, 600))

        edges = sample.filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(edges)
        mean_edge = float(stat.mean[0])

        histogram = edges.histogram()
        total = sum(histogram)
        strong = sum(histogram[80:])

        strong_ratio = (
            strong / total
            if total
            else 0.0
        )

        return mean_edge, strong_ratio

    records: list[dict[str, Any]] = []

    for item in scan_items:
        url = clean_text(item.get("url"))

        if not url:
            continue

        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            with Image.open(BytesIO(response.content)) as image:
                image = image.convert("RGB")
                width, height = image.size
                hash_value = dhash(image)
                mean_edge, strong_ratio = complexity(image)

            score = 0

            role = clean_text(item.get("role"))

            if role == "product_desktop":
                score += 25

            if height >= 1800:
                score += 15

            if height >= 2500:
                score += 10

            size_kb = len(response.content) // 1024

            if size_kb >= 1200:
                score += 10

            if strong_ratio >= 0.08:
                score += 20
            elif strong_ratio >= 0.04:
                score += 10

            if mean_edge >= 20:
                score += 15
            elif mean_edge >= 12:
                score += 8

            record = dict(item)
            record.update(
                {
                    "width": width,
                    "height": height,
                    "size_kb": size_kb,
                    "mean_edge": round(mean_edge, 4),
                    "strong_edge_ratio": round(strong_ratio, 6),
                    "perceptual_hash": str(hash_value),
                    "rank_score": score,
                }
            )

            records.append(record)

        except Exception as error:
            record = dict(item)
            record.update(
                {
                    "rank_score": 0,
                    "rank_error": clean_text(error),
                }
            )
            records.append(record)

    records.sort(
        key=lambda item: (
            int(item.get("rank_score") or 0),
            float(item.get("strong_edge_ratio") or 0),
            int(item.get("height") or 0),
        ),
        reverse=True,
    )

    # Conservative duplicate suppression using perceptual hash.
    selected: list[dict[str, Any]] = []
    selected_hashes: list[int] = []

    for item in records:
        hash_text = item.get("perceptual_hash")

        if hash_text in (None, ""):
            continue

        try:
            current_hash = int(hash_text)
        except (TypeError, ValueError):
            continue

        is_near_duplicate = any(
            (current_hash ^ existing_hash).bit_count() <= 6
            for existing_hash in selected_hashes
        )

        if is_near_duplicate:
            continue

        selected.append(item)
        selected_hashes.append(current_hash)

        if len(selected) >= top_n:
            break

    media_evidence["ranker_status"] = "success"
    media_evidence["ranker_scanned"] = len(records)
    media_evidence["ranked_images"] = records
    media_evidence["vision_candidates"] = selected
    media_evidence["vision_candidate_count"] = len(selected)

    return media_evidence



def prepare_vision_evidence_queue(
    media_evidence: dict[str, Any],
    expected_name: str,
    official_url: str,
) -> dict[str, Any]:
    """
    Prepare ranked image evidence for later multimodal extraction.

    This queue is evidence-only:
    - no image is published,
    - no extracted claim is treated as verified automatically,
    - target text language is normalized to English in a later stage.
    """

    if not isinstance(media_evidence, dict):
        return media_evidence

    candidates = media_evidence.get("vision_candidates", [])

    if not isinstance(candidates, list) or not candidates:
        media_evidence["vision_queue_status"] = "no_candidates"
        media_evidence["vision_evidence_queue"] = []
        return media_evidence

    queue: list[dict[str, Any]] = []

    for index, item in enumerate(candidates, 1):
        if not isinstance(item, dict):
            continue

        url = clean_text(item.get("url"))

        if not url:
            continue

        queue.append(
            {
                "evidence_id": f"media_{index:02d}",
                "product_name": expected_name,
                "official_page": official_url,
                "image_url": url,
                "image_path": clean_text(item.get("path")),
                "image_role": clean_text(item.get("role")),
                "rank_score": int(item.get("rank_score") or 0),
                "width": item.get("width"),
                "height": item.get("height"),
                "size_kb": item.get("size_kb"),
                "source_language": "auto_detect",
                "target_language": "en",
                "analysis_status": "pending",
                "claim_status": "not_extracted",
                "claims": [],
                "publish_image": False,
                "usage_mode": "internal_evidence_only",
            }
        )

    media_evidence["vision_queue_status"] = (
        "ready"
        if queue
        else "no_candidates"
    )
    media_evidence["vision_evidence_queue"] = queue
    media_evidence["vision_evidence_count"] = len(queue)

    return media_evidence



def empty_vision_claim(
    claim_id: str,
    source_image: str,
    source_language: str = "auto_detect",
) -> dict[str, Any]:
    """
    Return the canonical schema for a vision-derived evidence claim.

    Claims remain unverified until a later validation stage.
    """

    return {
        "claim_id": claim_id,
        "claim_type": "",
        "original_text": "",
        "english_text": "",
        "value": None,
        "unit": "",
        "confidence": 0,
        "source_image": source_image,
        "source_language": source_language,
        "evidence_status": "unverified",
        "product_identity_supported": False,
        "publish_allowed": False,
    }


def initialize_vision_claim_slots(
    media_evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Initialize claim containers for queued vision evidence.

    This does not perform OCR, translation, or verification.
    """

    if not isinstance(media_evidence, dict):
        return media_evidence

    queue = media_evidence.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        return media_evidence

    initialized = 0

    for item in queue:
        if not isinstance(item, dict):
            continue

        evidence_id = clean_text(item.get("evidence_id"))
        image_url = clean_text(item.get("image_url"))

        if not evidence_id or not image_url:
            continue

        if not isinstance(item.get("claims"), list):
            item["claims"] = []

        item["claim_schema_version"] = "1.0"
        item["claim_template"] = empty_vision_claim(
            claim_id=f"{evidence_id}_claim_01",
            source_image=image_url,
            source_language=clean_text(
                item.get("source_language")
            ) or "auto_detect",
        )
        initialized += 1

    media_evidence["vision_claim_schema_version"] = "1.0"
    media_evidence["vision_claim_slots_initialized"] = initialized

    return media_evidence



VISION_PROVIDER_NAMES = {
    "none",
    "local_ocr",
    "openai",
    "gemini",
    "custom",
}


def build_vision_provider_config(
    provider: str = "none",
) -> dict[str, Any]:
    """
    Return provider-neutral vision configuration.

    No network call is made here. Provider adapters may be added later
    without changing the evidence schema.
    """

    normalized = clean_text(provider).lower() or "none"

    if normalized not in VISION_PROVIDER_NAMES:
        normalized = "custom"

    return {
        "provider": normalized,
        "enabled": normalized != "none",
        "mode": "evidence_only",
        "target_language": "en",
        "auto_publish_claims": False,
        "publish_images": False,
        "requires_review": True,
    }


def vision_provider_analyze(
    evidence_item: dict[str, Any],
    provider_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Provider-neutral vision adapter entry point.

    Version 1 is intentionally a no-op adapter. It defines the contract
    that local OCR or external multimodal providers must follow.
    """

    result = {
        "status": "not_run",
        "provider": clean_text(
            provider_config.get("provider")
        ) or "none",
        "source_language": "auto_detect",
        "target_language": clean_text(
            provider_config.get("target_language")
        ) or "en",
        "raw_text": "",
        "claims": [],
        "error": "",
    }

    if not isinstance(evidence_item, dict):
        result["status"] = "invalid_evidence"
        result["error"] = "Evidence item must be an object"
        return result

    if provider_config.get("enabled") is not True:
        result["status"] = "provider_disabled"
        return result

    result["status"] = "adapter_not_implemented"
    result["error"] = (
        "Selected vision provider adapter has not been implemented yet"
    )

    return result


def attach_vision_provider_state(
    media_evidence: dict[str, Any],
    provider: str = "none",
) -> dict[str, Any]:
    """
    Attach provider configuration to the vision evidence queue without
    executing OCR or external AI calls.
    """

    if not isinstance(media_evidence, dict):
        return media_evidence

    config = build_vision_provider_config(provider)

    media_evidence["vision_provider"] = config

    queue = media_evidence.get("vision_evidence_queue", [])

    if isinstance(queue, list):
        for item in queue:
            if not isinstance(item, dict):
                continue

            item["vision_provider"] = config.get("provider")
            item["vision_analysis"] = {
                "status": "not_run",
                "provider": config.get("provider"),
                "claims": [],
                "raw_text": "",
            }

    return media_evidence



def build_vision_job_payload(
    product_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a provider-neutral vision analysis job payload.

    The payload is evidence-only and contains no authorization to publish
    source images or automatically approve claims.
    """

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        media = {}

    queue = media.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        queue = []

    jobs: list[dict[str, Any]] = []

    for item in queue:
        if not isinstance(item, dict):
            continue

        jobs.append(
            {
                "evidence_id": clean_text(
                    item.get("evidence_id")
                ),
                "product_name": clean_text(
                    item.get("product_name")
                ),
                "official_page": clean_text(
                    item.get("official_page")
                ),
                "image_url": clean_text(
                    item.get("image_url")
                ),
                "rank_score": int(
                    item.get("rank_score") or 0
                ),
                "source_language": clean_text(
                    item.get("source_language")
                ) or "auto_detect",
                "target_language": clean_text(
                    item.get("target_language")
                ) or "en",
                "analysis_status": clean_text(
                    item.get("analysis_status")
                ) or "pending",
                "claim_schema_version": clean_text(
                    item.get("claim_schema_version")
                ) or "1.0",
                "claim_template": item.get(
                    "claim_template",
                    {},
                ),
                "publish_image": False,
                "auto_publish_claims": False,
                "usage_mode": "internal_evidence_only",
            }
        )

    return {
        "schema_version": "1.0",
        "job_type": "vision_evidence_extraction",
        "product_id": clean_text(
            product_output.get("product_id")
        ),
        "product_name": clean_text(
            product_output.get("search_name")
        ),
        "official_url": clean_text(
            product_output.get("official_url")
        ),
        "provider": (
            media.get("vision_provider", {})
            .get("provider", "none")
            if isinstance(
                media.get("vision_provider", {}),
                dict,
            )
            else "none"
        ),
        "target_language": "en",
        "requires_review": True,
        "publish_images": False,
        "auto_publish_claims": False,
        "jobs": jobs,
        "job_count": len(jobs),
    }


def save_vision_job_payload(
    product_output: dict[str, Any],
    destination: Path,
) -> Path:
    """
    Save a provider-neutral vision job JSON file.
    """

    payload = build_vision_job_payload(
        product_output
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    return destination



def normalize_imported_vision_claim(
    claim: dict[str, Any],
    evidence_id: str,
    source_image: str,
    source_language: str,
) -> dict[str, Any]:
    """
    Normalize a provider-produced claim into the canonical vision schema.

    Imported claims remain unverified and cannot be auto-published.
    """

    if not isinstance(claim, dict):
        claim = {}

    confidence_raw = claim.get("confidence", 0)

    try:
        confidence = int(float(confidence_raw))
    except (TypeError, ValueError):
        confidence = 0

    confidence = max(0, min(confidence, 100))

    return {
        "claim_id": clean_text(
            claim.get("claim_id")
        ) or f"{evidence_id}_claim",
        "claim_type": clean_text(
            claim.get("claim_type")
        ),
        "original_text": clean_text(
            claim.get("original_text")
        ),
        "english_text": clean_text(
            claim.get("english_text")
        ),
        "value": claim.get("value"),
        "unit": clean_text(
            claim.get("unit")
        ),
        "confidence": confidence,
        "source_image": source_image,
        "source_language": clean_text(
            claim.get("source_language")
        ) or source_language or "auto_detect",
        "evidence_status": "unverified",
        "product_identity_supported": bool(
            claim.get("product_identity_supported")
        ),
        "publish_allowed": False,
    }


def import_vision_result_payload(
    product_output: dict[str, Any],
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge provider-neutral vision results into the queued media evidence.

    Safety rules:
    - evidence IDs must already exist in the queue,
    - imported claims remain unverified,
    - images remain non-publishable,
    - claims are never auto-promoted into specifications.
    """

    if not isinstance(product_output, dict):
        return product_output

    if not isinstance(result_payload, dict):
        return product_output

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        return product_output

    queue = media.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        return product_output

    queue_index = {
        clean_text(item.get("evidence_id")): item
        for item in queue
        if isinstance(item, dict)
        and clean_text(item.get("evidence_id"))
    }

    results = result_payload.get("results", [])

    if not isinstance(results, list):
        results = []

    imported_results = 0
    imported_claims = 0
    skipped_results = 0
    provenance_mismatches = 0

    for result in results:
        if not isinstance(result, dict):
            skipped_results += 1
            continue

        evidence_id = clean_text(
            result.get("evidence_id")
        )

        queue_item = queue_index.get(evidence_id)

        if queue_item is None:
            skipped_results += 1
            continue

        source_image = clean_text(
            queue_item.get("image_url")
        )

        queue_official_page = clean_text(
            queue_item.get("official_page")
        ) or clean_text(
            product_output.get("official_url")
        )

        result_source_image = clean_text(
            result.get("source_image")
        )

        result_official_page = clean_text(
            result.get("official_page")
        )

        # Strict provenance gate:
        # modern result payloads must match the current queued evidence.
        # Legacy payloads without provenance are treated as stale/unsafe.
        if not result_source_image:
            provenance_mismatches += 1
            skipped_results += 1
            continue

        if result_source_image != source_image:
            provenance_mismatches += 1
            skipped_results += 1
            continue

        if (
            result_official_page
            and queue_official_page
            and result_official_page != queue_official_page
        ):
            provenance_mismatches += 1
            skipped_results += 1
            continue

        source_language = clean_text(
            result.get("source_language")
        ) or clean_text(
            queue_item.get("source_language")
        ) or "auto_detect"

        provider = clean_text(
            result.get("provider")
        ) or clean_text(
            result_payload.get("provider")
        ) or "unknown"

        raw_text = clean_text(
            result.get("raw_text")
        )

        raw_claims = result.get("claims", [])

        if not isinstance(raw_claims, list):
            raw_claims = []

        normalized_claims: list[dict[str, Any]] = []

        for index, claim in enumerate(raw_claims, 1):
            normalized = normalize_imported_vision_claim(
                claim=claim,
                evidence_id=f"{evidence_id}_{index:02d}",
                source_image=source_image,
                source_language=source_language,
            )

            if not (
                normalized.get("original_text")
                or normalized.get("english_text")
                or normalized.get("claim_type")
            ):
                continue

            normalized_claims.append(normalized)

        queue_item["source_language"] = source_language
        queue_item["analysis_status"] = (
            "completed"
            if normalized_claims or raw_text
            else "no_evidence"
        )
        queue_item["claim_status"] = (
            "extracted_unverified"
            if normalized_claims
            else "not_extracted"
        )
        queue_item["claims"] = normalized_claims
        queue_item["publish_image"] = False
        queue_item["vision_provider"] = provider
        queue_item["vision_analysis"] = {
            "status": queue_item["analysis_status"],
            "provider": provider,
            "source_language": source_language,
            "target_language": "en",
            "raw_text": raw_text,
            "claim_count": len(normalized_claims),
        }

        imported_results += 1
        imported_claims += len(normalized_claims)

    media["vision_import_status"] = "completed"
    media["vision_imported_results"] = imported_results
    media["vision_imported_claims"] = imported_claims
    media["vision_skipped_results"] = skipped_results
    media["vision_provenance_mismatches"] = provenance_mismatches

    product_output["media_evidence"] = media

    evidence_summary = product_output.get("evidence_summary", {})

    if not isinstance(evidence_summary, dict):
        evidence_summary = {}

    evidence_summary["vision_import_status"] = (
        media.get("vision_import_status")
    )
    evidence_summary["vision_imported_results"] = imported_results
    evidence_summary["vision_imported_claims"] = imported_claims
    evidence_summary["vision_skipped_results"] = skipped_results
    evidence_summary["vision_provenance_mismatches"] = provenance_mismatches

    product_output["evidence_summary"] = evidence_summary

    return product_output


def load_vision_result_payload(
    path: Path,
) -> dict[str, Any]:
    """
    Load a provider-neutral vision result JSON file.
    """

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "Vision result file must contain a JSON object"
        )

    return payload



VISION_CLAIM_MIN_CONFIDENCE = 80


def validate_vision_claim(
    claim: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate one imported vision claim conservatively.

    A passing claim becomes review_ready, never auto-published.
    """

    if not isinstance(claim, dict):
        return {
            "status": "rejected",
            "reasons": ["Claim is not an object"],
        }

    reasons: list[str] = []

    claim_type = clean_text(
        claim.get("claim_type")
    )
    original_text = clean_text(
        claim.get("original_text")
    )
    english_text = clean_text(
        claim.get("english_text")
    )
    unit = clean_text(
        claim.get("unit")
    )

    try:
        confidence = int(
            float(claim.get("confidence") or 0)
        )
    except (TypeError, ValueError):
        confidence = 0

    if not claim_type:
        reasons.append("Missing claim type")

    if not original_text and not english_text:
        reasons.append("Missing claim text")

    if confidence < VISION_CLAIM_MIN_CONFIDENCE:
        reasons.append(
            f"Confidence below {VISION_CLAIM_MIN_CONFIDENCE}"
        )

    if claim.get("product_identity_supported") is not True:
        reasons.append("Product identity not supported")

    value = claim.get("value")

    if isinstance(value, (int, float)) and value < 0:
        reasons.append("Negative numeric value is not allowed")

    if unit and len(unit) > 20:
        reasons.append("Unit looks invalid")

    if english_text and len(english_text) > 500:
        reasons.append("English normalized text is too long")

    status = (
        "review_ready"
        if not reasons
        else "rejected"
    )

    return {
        "status": status,
        "reasons": reasons,
    }


def validate_vision_claims(
    product_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate all imported vision claims in the media evidence queue.

    Identity may inherit from a sufficiently matched official product page.
    Duplicate claims are suppressed.
    Conflicts are evaluated at semantic attribute level.
    """

    if not isinstance(product_output, dict):
        return product_output

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        return product_output

    queue = media.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        return product_output

    seen_keys: dict[
        tuple[str, str, str, str],
        dict[str, Any],
    ] = {}

    ready_count = 0
    rejected_count = 0
    duplicate_count = 0
    conflict_count = 0

    official_url = clean_text(
        product_output.get("official_url")
    )
    source_host = clean_text(
        product_output.get("source_host")
    )
    fetch_status = clean_text(
        product_output.get("fetch_status")
    ).lower()

    try:
        page_identity_score = float(
            product_output.get("page_identity_score") or 0.0
        )
    except (TypeError, ValueError):
        page_identity_score = 0.0

    official_media_context_supported = bool(
        official_url
        and source_host
        and fetch_status == "success"
        and page_identity_score >= 0.60
    )

    additive_claim_types = {
        "color_variant",
        "noise_cancellation_modes",
        "microphone_type",
        "supported_language",
        "supported_languages",
    }

    by_semantic_values: dict[str, set[str]] = {}
    semantic_claims: dict[str, list[dict[str, Any]]] = {}

    def conflict_key(
        claim_type: str,
        english_text: str,
    ) -> str:
        if claim_type in additive_claim_types:
            return ""

        if ":" in english_text:
            label = english_text.split(":", 1)[0]
            label = clean_text(label).lower()
            label = re.sub(
                r"[^a-z0-9]+",
                "_",
                label,
            ).strip("_")

            if label:
                return f"{claim_type}::{label}"

        return claim_type

    for item in queue:
        if not isinstance(item, dict):
            continue

        claims = item.get("claims", [])

        if not isinstance(claims, list):
            continue

        validated_claims: list[dict[str, Any]] = []

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            model_identity_supported = (
                claim.get("product_identity_supported") is True
            )

            claim["vision_model_identity_supported"] = (
                model_identity_supported
            )

            if (
                not model_identity_supported
                and official_media_context_supported
            ):
                claim["product_identity_supported"] = True
                claim["product_identity_support_source"] = (
                    "official_page_media_context"
                )
            elif model_identity_supported:
                claim["product_identity_support_source"] = (
                    "vision_model"
                )

            validation = validate_vision_claim(claim)

            claim["validation"] = validation
            claim["publish_allowed"] = False

            claim_type = clean_text(
                claim.get("claim_type")
            ).lower()

            english_text = clean_text(
                claim.get("english_text")
            ).lower()

            value_text = clean_text(
                claim.get("value")
            ).lower()

            unit_text = clean_text(
                claim.get("unit")
            ).lower()

            dedupe_key = (
                claim_type,
                english_text,
                value_text,
                unit_text,
            )

            if dedupe_key in seen_keys:
                claim["validation"] = {
                    "status": "duplicate",
                    "reasons": [
                        "Duplicate of an already imported claim"
                    ],
                }
                claim["evidence_status"] = "duplicate"
                duplicate_count += 1
                validated_claims.append(claim)
                continue

            seen_keys[dedupe_key] = claim

            if validation["status"] == "review_ready":
                claim["evidence_status"] = "review_ready"
                ready_count += 1
            else:
                claim["evidence_status"] = "rejected"
                rejected_count += 1

            current_key = conflict_key(
                claim_type,
                english_text,
            )

            if (
                validation["status"] == "review_ready"
                and current_key
                and value_text
            ):
                by_semantic_values.setdefault(
                    current_key,
                    set(),
                ).add(
                    f"{value_text}|{unit_text}"
                )
                semantic_claims.setdefault(
                    current_key,
                    [],
                ).append(claim)

            validated_claims.append(claim)

        item["claims"] = validated_claims

    conflicting_keys = {
        key
        for key, values in by_semantic_values.items()
        if len(values) > 1
    }

    if conflicting_keys:
        for key in conflicting_keys:
            for claim in semantic_claims.get(key, []):
                validation = claim.get("validation", {})

                if not isinstance(validation, dict):
                    validation = {}

                if validation.get("status") != "review_ready":
                    continue

                reasons = validation.get("reasons", [])

                if not isinstance(reasons, list):
                    reasons = []

                reasons.append(
                    "Conflicting values found for same semantic attribute"
                )

                validation["status"] = "manual_review"
                validation["reasons"] = reasons

                claim["validation"] = validation
                claim["evidence_status"] = "manual_review"

                ready_count = max(0, ready_count - 1)
                conflict_count += 1

    for item in queue:
        if not isinstance(item, dict):
            continue

        claims = item.get("claims", [])

        if not isinstance(claims, list):
            continue

        statuses = {
            clean_text(
                claim.get("evidence_status")
            )
            for claim in claims
            if isinstance(claim, dict)
        }

        if "review_ready" in statuses:
            item["claim_status"] = "review_ready"
        elif "manual_review" in statuses:
            item["claim_status"] = "manual_review"
        elif "duplicate" in statuses and len(statuses) == 1:
            item["claim_status"] = "duplicate"
        elif claims:
            item["claim_status"] = "rejected"
        else:
            item["claim_status"] = "not_extracted"

    media["vision_validation_status"] = "completed"
    media["vision_review_ready_claims"] = ready_count
    media["vision_rejected_claims"] = rejected_count
    media["vision_duplicate_claims"] = duplicate_count
    media["vision_conflicting_claims"] = conflict_count
    media["vision_identity_context_inheritance"] = (
        official_media_context_supported
    )

    product_output["media_evidence"] = media

    summary = product_output.get("evidence_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    summary["vision_validation_status"] = (
        media.get("vision_validation_status")
    )
    summary["vision_review_ready_claims"] = ready_count
    summary["vision_rejected_claims"] = rejected_count
    summary["vision_duplicate_claims"] = duplicate_count
    summary["vision_conflicting_claims"] = conflict_count
    summary["vision_identity_context_inheritance"] = (
        official_media_context_supported
    )

    product_output["evidence_summary"] = summary

    return product_output


UNIVERSAL_SEMANTIC_SCHEMA_VERSION = "1.3"

UNIVERSAL_SEMANTIC_ALLOWED_CATEGORIES = {
    "identity",
    "count",
    "distance",
    "duration",
    "latency",
    "capacity",
    "rating",
    "version",
    "codec",
    "certification",
    "technology",
    "feature",
    "interface",
    "variant",
    "dimension",
    "weight",
    "power",
    "performance",
    "compatibility",
    "material_property",
    "other",
}


def build_universal_semantic_input(
    product_output: dict[str, Any],
) -> dict[str, Any]:
    claims: list[dict[str, Any]] = []

    media = product_output.get("media_evidence", {})

    if isinstance(media, dict):
        queue = media.get("vision_evidence_queue", [])

        if isinstance(queue, list):
            for item in queue:
                if not isinstance(item, dict):
                    continue

                evidence_id = clean_text(item.get("evidence_id"))
                item_claims = item.get("claims", [])

                if not isinstance(item_claims, list):
                    continue

                for claim in item_claims:
                    if not isinstance(claim, dict):
                        continue

                    if clean_text(claim.get("evidence_status")) != "review_ready":
                        continue

                    claims.append(
                        {
                            "claim_id": clean_text(claim.get("claim_id")),
                            "evidence_id": evidence_id,
                            "claim_type": clean_text(claim.get("claim_type")),
                            "english_text": clean_text(claim.get("english_text")),
                            "value": claim.get("value"),
                            "unit": clean_text(claim.get("unit")),
                            "confidence": claim.get("confidence"),
                            "source_language": clean_text(claim.get("source_language")),
                        }
                    )

    return {
        "schema_version": UNIVERSAL_SEMANTIC_SCHEMA_VERSION,
        "job_type": "universal_semantic_consolidation",
        "product_id": clean_text(product_output.get("product_id")),
        "product_name": clean_text(
            product_output.get("search_name")
            or product_output.get("model")
        ),
        "input_claim_count": len(claims),
        "claims": claims,
    }


def build_universal_semantic_prompt() -> str:
    categories = ", ".join(
        sorted(UNIVERSAL_SEMANTIC_ALLOWED_CATEGORIES)
    )

    return f"""
You are a UNIVERSAL product-fact semantic consolidator.

Input: validated factual claims for one product from official evidence.

Your output must work across many product categories and must NOT contain
product-specific hard-coded rules.

ALLOWED FACT CATEGORIES:
{categories}

STRICT SEMANTIC RULES:
1. Group claims only when they represent the same underlying fact.
2. Preserve all meaningful qualifiers and operators:
   <, <=, >, >=, up to, over, more than, approximately, test conditions,
   modes, per-unit scope, standalone scope, total scope, with-case scope.
3. Never convert a bounded or qualified measurement into an exact value.
4. Preserve compound facts in structured_value.
5. Preserve additive values as arrays.
6. Compatible relational facts are not conflicts.
7. Genuine contradictions must be marked conflict_status="conflict".
8. Do not invent missing facts.
9. Keep all evidence_ids and source_claim_ids.
10. Canonical keys must be generic, machine-friendly and brand/model independent.
11. Separate codecs, certifications, technologies, interfaces and features.
12. Source images remain evidence only.

MANDATORY TAXONOMY RULES:
- Product/model/name identity facts -> fact_category = "identity".
- Physical operating/transmission range facts -> "distance".
- Physical component sizes/dimensions -> "dimension".
- Material composition/purity/property percentages -> "material_property".
- Playback/charging/runtime measured in time -> "duration".
- Signal/input/output delay measured in ms -> "latency".
- Battery/storage capacities -> "capacity".
- Counts of devices/microphones/languages/items -> "count".
- Bluetooth/software/protocol revision numbers -> "version".
- Audio/data codecs -> "codec".
- Certification labels -> "certification".
- IP/protection/performance grades -> "rating" when applicable.
- Colors/finishes/options -> "variant".
- Connector/port standards -> "interface".
- Algorithms, driver systems and named technical mechanisms -> "technology".
- Boolean capability/integration/support -> "feature".

SOURCE OPERATOR FIDELITY:
- Preserve the semantic operator actually stated by the source.
- "up to X" -> operator "up to"; do not rewrite as "<=".
- "<=X" -> operator "<="; do not rewrite as "up to".
- "over X" / "more than X" -> preserve that meaning.
- Never infer an operator from the numeric value alone.
- If multiple equivalent evidence items use different wording, prefer the
  most explicit operator from the strongest direct evidence.

Return JSON only:
{{
  "schema_version": "1.3",
  "product_name": "",
  "input_claim_count": 0,
  "canonical_fact_count": 0,
  "facts": [
    {{
      "canonical_key": "",
      "fact_category": "",
      "normalized_summary": "",
      "value": null,
      "unit": "",
      "operator": "",
      "qualifier": "",
      "values": [],
      "structured_value": {{}},
      "confidence": 0,
      "evidence_ids": [],
      "source_claim_ids": [],
      "conflict_status": "none",
      "requires_review": false
    }}
  ]
}}
""".strip()


def validate_universal_semantic_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    if not isinstance(result, dict):
        return {
            "status": "failed",
            "issue_count": 1,
            "issues": [{"canonical_key": "", "reasons": ["Semantic result is not a dictionary"]}],
        }

    facts = result.get("facts", [])

    if not isinstance(facts, list):
        return {
            "status": "failed",
            "issue_count": 1,
            "issues": [{"canonical_key": "", "reasons": ["facts must be a list"]}],
        }

    for fact in facts:
        if not isinstance(fact, dict):
            issues.append({"canonical_key": "", "reasons": ["Fact entry is not an object"]})
            continue

        key = clean_text(fact.get("canonical_key")).lower()
        category = clean_text(fact.get("fact_category")).lower()
        unit = clean_text(fact.get("unit")).lower()
        operator = clean_text(fact.get("operator")).lower()
        structured_value = fact.get("structured_value")
        evidence_ids = fact.get("evidence_ids")
        source_claim_ids = fact.get("source_claim_ids")

        reasons: list[str] = []

        if not key:
            reasons.append("canonical_key is empty")

        if category not in UNIVERSAL_SEMANTIC_ALLOWED_CATEGORIES:
            reasons.append(f"Unsupported fact category: {category}")

        if structured_value is not None and not isinstance(structured_value, dict):
            reasons.append("structured_value must be an object")

        if not isinstance(evidence_ids, list) or not evidence_ids:
            reasons.append("Missing supporting evidence_ids")

        if not isinstance(source_claim_ids, list) or not source_claim_ids:
            reasons.append("Missing source_claim_ids")

        if key in {"product_name", "model_name"} or "identity" in key:
            if category != "identity":
                reasons.append("Identity fact must use identity category")

        if (
            any(token in key for token in {"range", "distance"})
            and unit in {"mm", "cm", "m", "km"}
            and category != "distance"
        ):
            reasons.append("Range/distance fact must use distance category")

        if (
            any(
                token in key
                for token in {
                    "diameter",
                    "width",
                    "height",
                    "length",
                    "thickness",
                    "size",
                }
            )
            and unit in {"mm", "cm", "m"}
            and category not in {"dimension", "distance"}
        ):
            reasons.append("Physical size fact must use dimension/distance category")

        if "latency" in key and unit == "ms" and category != "latency":
            reasons.append("Latency measured in ms must use latency category")

        if unit in {"mah", "wh", "kwh"} and category != "capacity":
            reasons.append("Capacity unit requires capacity category")

        if "codec" in key and category != "codec":
            reasons.append("Codec fact must use codec category")

        if "certification" in key and category != "certification":
            reasons.append("Certification fact must use certification category")

        if "purity" in key and unit == "%" and category != "material_property":
            reasons.append("Purity percentage must use material_property category")

        allowed_operators = {
            "",
            "<",
            "<=",
            ">",
            ">=",
            "up to",
            "over",
            "more than",
            "approximately",
        }

        if operator not in allowed_operators:
            reasons.append(f"Unsupported operator: {operator}")

        if reasons:
            issues.append(
                {
                    "canonical_key": key,
                    "reasons": reasons,
                }
            )

    return {
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "fact_count": len(facts),
        "schema_version": clean_text(result.get("schema_version")),
    }


def attach_universal_semantic_result(
    product_output: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    validation = validate_universal_semantic_result(result)

    product_output["semantic_consolidation"] = {
        "schema_version": UNIVERSAL_SEMANTIC_SCHEMA_VERSION,
        "status": (
            "ready_for_review"
            if validation.get("status") == "passed"
            else "rejected"
        ),
        "validation": validation,
        "result": result,
        "auto_publish": False,
        "requires_review": True,
    }

    summary = product_output.get("evidence_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    summary["semantic_consolidation_status"] = (
        product_output["semantic_consolidation"]["status"]
    )
    summary["semantic_fact_count"] = validation.get("fact_count", 0)
    summary["semantic_validation_issues"] = validation.get("issue_count", 0)

    product_output["evidence_summary"] = summary

    return product_output



def promote_reviewed_vision_claims(
    product_output: dict[str, Any],
    approved_claim_ids: list[str] | set[str] | tuple[str, ...],
) -> dict[str, Any]:
    # Promote only explicitly approved, review-ready claims.
    # Source images remain internal evidence and are never made publishable here.

    if not isinstance(product_output, dict):
        return product_output

    approved_ids = {
        clean_text(value)
        for value in approved_claim_ids
        if clean_text(value)
    }

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        return product_output

    queue = media.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        return product_output

    promoted = 0
    blocked = 0

    for item in queue:
        if not isinstance(item, dict):
            continue

        item["publish_image"] = False

        claims = item.get("claims", [])

        if not isinstance(claims, list):
            continue

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            claim_id = clean_text(claim.get("claim_id"))
            validation = claim.get("validation", {})

            validation_status = (
                clean_text(validation.get("status"))
                if isinstance(validation, dict)
                else ""
            )

            eligible = (
                claim_id in approved_ids
                and validation_status == "review_ready"
                and claim.get("product_identity_supported") is True
                and bool(clean_text(claim.get("english_text")))
            )

            if eligible:
                claim["evidence_status"] = "approved_for_knowledge"
                claim["publish_allowed"] = True
                claim["promotion_status"] = "approved"
                claim["promotion_reason"] = (
                    "Explicit approval after successful vision claim validation"
                )
                promoted += 1
            else:
                claim["publish_allowed"] = False

                if claim_id in approved_ids:
                    claim["promotion_status"] = "blocked"
                    claim["promotion_reason"] = (
                        "Claim did not satisfy promotion gate requirements"
                    )
                    blocked += 1

        statuses = {
            clean_text(claim.get("evidence_status"))
            for claim in claims
            if isinstance(claim, dict)
        }

        if "approved_for_knowledge" in statuses:
            item["claim_status"] = "approved_for_knowledge"

    media["vision_promotion_status"] = "completed"
    media["vision_promoted_claims"] = promoted
    media["vision_blocked_promotions"] = blocked
    media["vision_images_publishable"] = False

    product_output["media_evidence"] = media

    summary = product_output.get("evidence_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    summary["vision_promotion_status"] = "completed"
    summary["vision_promoted_claims"] = promoted
    summary["vision_blocked_promotions"] = blocked
    summary["vision_images_publishable"] = False

    product_output["evidence_summary"] = summary

    return product_output



def build_vision_knowledge_candidates(
    product_output: dict[str, Any],
) -> dict[str, Any]:
    # Convert explicitly promoted vision claims into knowledge candidates.
    # This function does not publish source images and does not write to the
    # final verified knowledge database.

    if not isinstance(product_output, dict):
        return product_output

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        return product_output

    queue = media.get("vision_evidence_queue", [])

    if not isinstance(queue, list):
        return product_output

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for item in queue:
        if not isinstance(item, dict):
            continue

        evidence_id = clean_text(item.get("evidence_id"))
        image_url = clean_text(item.get("image_url"))
        claims = item.get("claims", [])

        if not isinstance(claims, list):
            continue

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            if claim.get("evidence_status") != "approved_for_knowledge":
                continue

            if claim.get("publish_allowed") is not True:
                continue

            claim_type = clean_text(claim.get("claim_type"))
            english_text = clean_text(claim.get("english_text"))
            unit = clean_text(claim.get("unit"))
            value = claim.get("value")

            if not claim_type or not english_text:
                continue

            dedupe_key = (
                claim_type.lower(),
                english_text.lower(),
                clean_text(value).lower(),
                unit.lower(),
            )

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)

            candidates.append(
                {
                    "knowledge_id": clean_text(
                        claim.get("claim_id")
                    ),
                    "claim_type": claim_type,
                    "text": english_text,
                    "value": value,
                    "unit": unit,
                    "confidence": int(
                        claim.get("confidence") or 0
                    ),
                    "source_type": "official_image_evidence",
                    "source_page": clean_text(
                        product_output.get("official_url")
                    ),
                    "source_image": image_url,
                    "source_evidence_id": evidence_id,
                    "source_language": clean_text(
                        claim.get("source_language")
                    ) or "auto_detect",
                    "product_identity_supported": (
                        claim.get("product_identity_supported") is True
                    ),
                    "knowledge_status": "candidate",
                    "requires_final_review": True,
                    "publish_source_image": False,
                }
            )

    media["vision_knowledge_bridge_status"] = "completed"
    media["vision_knowledge_candidates"] = candidates
    media["vision_knowledge_candidate_count"] = len(candidates)

    product_output["media_evidence"] = media

    summary = product_output.get("evidence_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    summary["vision_knowledge_bridge_status"] = "completed"
    summary["vision_knowledge_candidate_count"] = len(candidates)

    product_output["evidence_summary"] = summary

    return product_output



def finalize_vision_knowledge_candidates(
    product_output: dict[str, Any],
    approved_knowledge_ids: list[str] | set[str] | tuple[str, ...],
) -> dict[str, Any]:
    # Final manual review gate for vision-derived knowledge candidates.
    # Passing this gate makes a candidate eligible for knowledge ingestion,
    # but does not itself write to the final knowledge database.

    if not isinstance(product_output, dict):
        return product_output

    approved_ids = {
        clean_text(value)
        for value in approved_knowledge_ids
        if clean_text(value)
    }

    media = product_output.get("media_evidence", {})

    if not isinstance(media, dict):
        return product_output

    candidates = media.get("vision_knowledge_candidates", [])

    if not isinstance(candidates, list):
        return product_output

    verified = 0
    blocked = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        knowledge_id = clean_text(
            candidate.get("knowledge_id")
        )

        eligible = (
            knowledge_id in approved_ids
            and candidate.get("knowledge_status") == "candidate"
            and candidate.get("requires_final_review") is True
            and candidate.get("product_identity_supported") is True
            and bool(clean_text(candidate.get("text")))
            and int(candidate.get("confidence") or 0) >= 80
        )

        candidate["publish_source_image"] = False

        if eligible:
            candidate["knowledge_status"] = (
                "verified_for_knowledge_ingestion"
            )
            candidate["requires_final_review"] = False
            candidate["final_review_status"] = "approved"
            candidate["final_review_reason"] = (
                "Explicit final approval after vision evidence validation"
            )
            verified += 1
        elif knowledge_id in approved_ids:
            candidate["final_review_status"] = "blocked"
            candidate["final_review_reason"] = (
                "Candidate did not satisfy final knowledge review requirements"
            )
            blocked += 1

    media["vision_final_review_status"] = "completed"
    media["vision_verified_knowledge_candidates"] = verified
    media["vision_blocked_knowledge_candidates"] = blocked
    media["vision_images_publishable"] = False

    product_output["media_evidence"] = media

    summary = product_output.get("evidence_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    summary["vision_final_review_status"] = "completed"
    summary["vision_verified_knowledge_candidates"] = verified
    summary["vision_blocked_knowledge_candidates"] = blocked
    summary["vision_images_publishable"] = False

    product_output["evidence_summary"] = summary

    return product_output


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
        "media_evidence": {
            "collector": "",
            "total_images": 0,
            "product_image_count": 0,
            "desktop_count": 0,
            "mobile_count": 0,
            "generic_candidate_count": 0,
            "excluded_ui_assets": 0,
            "product_images": [],
            "ui_assets": [],
            "ocr_status": "not_run",
            "vision_status": "not_run",
        },
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

    output["media_evidence"] = collect_embedded_media_evidence(
        html
    )

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
    structured_section_count = extract_structured_sections(
        soup,
        specifications,
    )
    embedded_state_count = extract_embedded_state_specs(
        html,
        specifications,
    )
    shopify_oxygen_count = extract_shopify_oxygen_specs(
        html,
        specifications,
    )
    apple_techspecs_count = extract_apple_techspecs(
        soup,
        specifications,
        official_url,
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
        "structured_section_specifications": structured_section_count,
        "embedded_state_specifications": embedded_state_count,
        "shopify_oxygen_specifications": shopify_oxygen_count,
        "apple_techspecs_specifications": apple_techspecs_count,
        "total_specifications": len(specifications),
        "feature_items": len(features),
        "media_product_images": output.get(
            "media_evidence",
            {},
        ).get("product_image_count", 0),
        "media_ui_assets": output.get(
            "media_evidence",
            {},
        ).get("excluded_ui_assets", 0),
        "noise_filter_version": "2.0",
    }

    evidence_count = len(specifications) + len(features)

    if (
        evidence_count < 3
        and output.get("media_evidence", {}).get(
            "product_image_count",
            0,
        ) > 0
    ):
        output["media_evidence"] = rank_media_evidence(
            output.get("media_evidence", {}),
        )

        output["media_evidence"] = prepare_vision_evidence_queue(
            output.get("media_evidence", {}),
            expected_name,
            official_url,
        )

        output["media_evidence"] = initialize_vision_claim_slots(
            output.get("media_evidence", {}),
        )

        output["media_evidence"] = attach_vision_provider_state(
            output.get("media_evidence", {}),
            provider="none",
        )

        output["evidence_summary"]["media_ranker_status"] = (
            output.get("media_evidence", {}).get("ranker_status")
        )
        output["evidence_summary"]["vision_candidate_count"] = (
            output.get("media_evidence", {}).get(
                "vision_candidate_count",
                0,
            )
        )
        output["evidence_summary"]["vision_queue_status"] = (
            output.get("media_evidence", {}).get(
                "vision_queue_status"
            )
        )
        output["evidence_summary"]["vision_evidence_count"] = (
            output.get("media_evidence", {}).get(
                "vision_evidence_count",
                0,
            )
        )
        output["evidence_summary"]["vision_claim_schema_version"] = (
            output.get("media_evidence", {}).get(
                "vision_claim_schema_version"
            )
        )
        output["evidence_summary"]["vision_claim_slots_initialized"] = (
            output.get("media_evidence", {}).get(
                "vision_claim_slots_initialized",
                0,
            )
        )
        output["evidence_summary"]["vision_provider"] = (
            output.get("media_evidence", {})
            .get("vision_provider", {})
            .get("provider")
        )

    if (
        output["resolver_verified"] is True
        and (
            match_score >= 0.80
            or (
                (
                    structured_section_count
                    + apple_techspecs_count
                ) >= 5
                and match_score >= 0.70
            )
        )
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

    if not research_result.get("_single_source_only"):
        source_attempts: list[dict[str, Any]] = []
        current_url = clean_text(output.get("official_url"))
        current_evidence = (
            len(output.get("specifications", {}))
            + len(output.get("features", []))
        )

        if current_evidence < 3:
            for source in collect_official_source_urls(research_result):
                source_url = clean_text(source.get("url"))

                if not source_url or source_url == current_url:
                    continue

                alternate_result_input = dict(research_result)
                alternate_result_input["official_url"] = source_url
                alternate_result_input["_single_source_only"] = True

                alternate = extract_one(
                    alternate_result_input,
                    identity,
                )

                source_attempts.append(
                    {
                        "url": source_url,
                        "source_type": source.get("source_type"),
                        "fetch_status": alternate.get("fetch_status"),
                        "page_identity_score": alternate.get(
                            "page_identity_score"
                        ),
                        "specification_count": len(
                            alternate.get("specifications", {})
                        ),
                        "feature_count": len(
                            alternate.get("features", [])
                        ),
                        "review_status": alternate.get(
                            "review",
                            {},
                        ).get("status"),
                    }
                )

                merge_evidence_records(
                    output,
                    alternate,
                )

                output["page_identity_score"] = max(
                    float(output.get("page_identity_score") or 0),
                    float(alternate.get("page_identity_score") or 0),
                )

                if (
                    len(output.get("specifications", {}))
                    + len(output.get("features", []))
                ) >= 3:
                    break

        summary = output.setdefault("evidence_summary", {})
        summary["source_attempts"] = source_attempts
        summary["sources_attempted"] = 1 + len(source_attempts)
        summary["total_specifications"] = len(
            output.get("specifications", {})
        )
        summary["feature_items"] = len(
            output.get("features", [])
        )

        apply_review_decision(output)

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


def run_universal_semantic_cli(
    product_ids: list[str],
    limit: int | None = None,
) -> int:
    """
    Run universal semantic consolidation for selected stored products.

    Gemini is only the current provider adapter. Semantic schema,
    validation and attach logic remain provider-neutral.
    """
    import copy
    import os

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "ERROR: Google GenAI package is not installed.",
            file=sys.stderr,
        )
        return 1

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print(
            "ERROR: GEMINI_API_KEY is not set.",
            file=sys.stderr,
        )
        return 1

    if not OUTPUT_DB.exists():
        print(
            f"ERROR: Missing official specs database: {OUTPUT_DB}",
            file=sys.stderr,
        )
        return 1

    try:
        stored = load_json(OUTPUT_DB, {})
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    products = stored.get("products", [])

    if not isinstance(products, list):
        print("ERROR: Invalid products database.", file=sys.stderr)
        return 1

    selected_ids = {
        clean_text(value)
        for value in product_ids
        if clean_text(value)
    }

    selected = []

    for product in products:
        if not isinstance(product, dict):
            continue

        product_id = clean_text(product.get("product_id"))

        if selected_ids and product_id not in selected_ids:
            continue

        selected.append(product)

    if limit is not None:
        selected = selected[: max(0, int(limit))]

    if not selected:
        print("No eligible products selected for semantic consolidation.")
        return 0

    client = genai.Client(api_key=api_key)

    semantic_dir = ROOT / "data" / "semantic_results"
    vision_dir = ROOT / "data" / "vision_results"

    semantic_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    passed = 0
    failed = 0
    skipped = 0
    semantic_state_updates = 0

    for product in selected:
        product_id = clean_text(product.get("product_id"))
        product_name = clean_text(
            product.get("search_name")
            or product.get("model")
            or product.get("title")
        )

        print()
        print("=" * 72)
        print("SEMANTIC:", product_id, "|", product_name)
        print("=" * 72)

        working = copy.deepcopy(product)

        combined = {
            "provider": "gemini",
            "results": [],
        }

        result_files = sorted(
            vision_dir.glob(
                f"product_{product_id}_media_*.json"
            )
        )

        for path in result_files:
            try:
                payload = load_json(path, {})
            except (OSError, ValueError) as error:
                print(
                    f"WARNING: Could not read {path}: {error}"
                )
                continue

            results = payload.get("results", [])

            if isinstance(results, list):
                combined["results"].extend(results)

        if combined["results"]:
            working = import_vision_result_payload(
                working,
                combined,
            )
            working = validate_vision_claims(working)

        semantic_input = build_universal_semantic_input(
            working
        )

        claim_count = int(
            semantic_input.get("input_claim_count", 0)
            or 0
        )

        print("Validated claims :", claim_count)

        if claim_count <= 0:
            print(
                "SKIP: No review-ready claims available."
            )

            # Persist updated vision/provenance state even when semantic
            # consolidation cannot run. This prevents stale or mismatched
            # evidence from being reported later as complete.
            product_index = products.index(product)
            products[product_index] = working
            semantic_state_updates += 1

            skipped += 1
            continue

        prompt = build_universal_semantic_prompt()

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    prompt,
                    "\nINPUT CLAIMS:\n",
                    json.dumps(
                        semantic_input,
                        ensure_ascii=False,
                    ),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )

            semantic_result = json.loads(response.text)

        except Exception as error:
            print(
                "ERROR: Semantic provider failed:",
                type(error).__name__,
                str(error)[:300],
            )
            failed += 1
            continue

        validation = validate_universal_semantic_result(
            semantic_result
        )

        out_path = (
            semantic_dir
            / f"product_{product_id}_semantic_v1_3.json"
        )

        save_json(out_path, semantic_result)

        print(
            "Canonical facts :",
            validation.get("fact_count", 0),
        )
        print(
            "Schema issues   :",
            validation.get("issue_count", 0),
        )
        print(
            "Validation      :",
            validation.get("status"),
        )
        print("Saved           :", out_path)

        product_index = products.index(product)

        products[product_index] = (
            attach_universal_semantic_result(
                working,
                semantic_result,
            )
        )

        processed += 1

        if validation.get("status") == "passed":
            passed += 1
        else:
            failed += 1

    stored["products"] = products

    if processed or semantic_state_updates:
        try:
            backup = backup_output()
            save_json(OUTPUT_DB, stored)
        except (OSError, ValueError) as error:
            print(
                f"ERROR: Could not save semantic results: {error}",
                file=sys.stderr,
            )
            return 1

        print()
        print("Backup          :", backup)

    print()
    print("=" * 72)
    print("UNIVERSAL SEMANTIC CONSOLIDATION COMPLETE")
    print("=" * 72)
    print("Processed :", processed)
    print("Passed    :", passed)
    print("Failed    :", failed)
    print("Skipped   :", skipped)
    print("State saved:", semantic_state_updates)
    print("Auto-publish: NO")
    print("Review gate : REQUIRED")

    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract review-ready product specifications from official pages"
        )
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=("extract", "semantic", "status"),
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

    if args.command == "semantic":
        return run_universal_semantic_cli(
            product_ids=args.product_id,
            limit=args.limit,
        )

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


