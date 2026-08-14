#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
COUPONS = ROOT / "coupons.json"
RESEARCH = ROOT / "data" / "research_results.json"
SPECS = ROOT / "data" / "official_specs.json"
OUTPUT = ROOT / "data" / "image_coverage_candidates.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131 Safari/537.36"
    )
}

STOP = {
    "the", "and", "for", "with", "from", "pack", "black",
    "white", "blue", "gold", "storage", "ram", "gb",
    "online", "store", "latest", "offer", "product",
}

BAD_IMAGE_TOKENS = (
    "logo", "favicon", "sprite", "placeholder",
    "icon-", "/icon/", "social-share", "loading.gif",
)

BAD_PAGE_TOKENS = (
    "/search",
    "/s?",
    "?k=",
    "/offers",
    "/deals",
)

IMAGE_KEYS = {
    "image", "images", "imageurl", "image_url",
    "thumbnail", "thumbnailurl", "primaryimage",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def product_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        for key in ("products", "coupons", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

    return []


def clean(value: Any) -> str:
    return str(value or "").strip()


def tokens(value: str) -> set[str]:
    raw = re.findall(r"[a-z0-9]+", value.lower())

    return {
        x
        for x in raw
        if len(x) >= 2 and x not in STOP
    }


def core_tokens(title: str) -> set[str]:
    all_tokens = tokens(title)

    model = {
        x
        for x in all_tokens
        if any(c.isdigit() for c in x)
        or x in {
            "iphone", "airpods", "kindle", "echo",
            "galaxy", "redmi", "realme", "oneplus",
            "jbl", "inspiron", "colorfit", "airdopes",
            "rockerz", "fire", "nothing",
        }
    }

    return model or set(list(all_tokens)[:8])


def identity_score(expected: str, candidate: str) -> float:
    expected_tokens = core_tokens(expected)
    candidate_tokens = tokens(candidate)

    if not expected_tokens or not candidate_tokens:
        return 0.0

    return len(
        expected_tokens.intersection(candidate_tokens)
    ) / len(expected_tokens)


def valid_image_url(url: str) -> bool:
    value = clean(url)

    if not value.startswith(("http://", "https://")):
        return False

    lowered = value.lower()

    return not any(
        token in lowered
        for token in BAD_IMAGE_TOKENS
    )


def add_image(
    found: list[dict[str, Any]],
    seen: set[str],
    url: Any,
    source: str,
) -> None:

    if isinstance(url, list):
        for item in url:
            add_image(found, seen, item, source)
        return

    if isinstance(url, dict):
        for key in ("url", "contentUrl", "thumbnailUrl"):
            if key in url:
                add_image(found, seen, url.get(key), source)
        return

    value = clean(url)

    if not valid_image_url(value):
        return

    if value in seen:
        return

    seen.add(value)

    found.append(
        {
            "url": value,
            "source": source,
        }
    )


def jsonld_images(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:

    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text("", strip=False)

        if not raw:
            continue

        try:
            payload = json.loads(raw)
        except Exception:
            continue

        stack = [payload]

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
            types = (
                item_type
                if isinstance(item_type, list)
                else [item_type]
            )

            is_product = any(
                clean(value).lower()
                in {
                    "product",
                    "productmodel",
                    "individualproduct",
                }
                for value in types
            )

            if not is_product:
                continue

            for key, value in current.items():
                if clean(key).lower() in IMAGE_KEYS:
                    add_image(
                        found,
                        seen,
                        value,
                        "product_jsonld",
                    )

    return found


def html_meta_images(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:

    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for attribute, name in (
        ("property", "og:image:secure_url"),
        ("property", "og:image"),
        ("name", "twitter:image"),
        ("name", "twitter:image:src"),
    ):
        tag = soup.find(
            "meta",
            attrs={attribute: name},
        )

        if tag:
            add_image(
                found,
                seen,
                tag.get("content"),
                f"meta:{name}",
            )

    return found


def fetch_page(
    url: str,
) -> tuple[str, str, int]:

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=(6, 18),
            allow_redirects=True,
        )

        return (
            response.text,
            response.url,
            response.status_code,
        )

    except Exception:
        return "", url, 0


def page_candidates(
    title: str,
    url: str,
) -> dict[str, Any] | None:

    if not url:
        return None

    lowered = url.lower()

    if any(
        token in lowered
        for token in BAD_PAGE_TOKENS
    ):
        return None

    html, final_url, status = fetch_page(url)

    if status != 200 or not html:
        return None

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    page_title = ""

    if soup.title:
        page_title = clean(
            soup.title.get_text(" ", strip=True)
        )

    h1 = soup.find("h1")

    identity_text = " ".join(
        [
            page_title,
            clean(
                h1.get_text(" ", strip=True)
            ) if h1 else "",
            final_url,
        ]
    )

    match = identity_score(
        title,
        identity_text,
    )

    images = jsonld_images(soup)

    if not images:
        images = html_meta_images(soup)

    return {
        "page_url": final_url,
        "status_code": status,
        "page_title": page_title,
        "identity_score": round(match, 3),
        "images": images[:10],
    }


def build_url_index(
    research_data: Any,
    specs_data: Any,
) -> dict[str, list[dict[str, str]]]:

    index: dict[str, list[dict[str, str]]] = {}

    for source_name, data in (
        ("research", research_data),
        ("spec", specs_data),
    ):
        for item in product_list(data):
            pid = clean(
                item.get("product_id")
                or item.get("id")
            )

            if not pid:
                continue

            url = clean(
                item.get("official_url")
                or item.get("url")
                or item.get("source_url")
            )

            if not url:
                continue

            index.setdefault(pid, []).append(
                {
                    "url": url,
                    "source": source_name,
                }
            )

    return index


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    args = parser.parse_args()

    products = product_list(
        load_json(COUPONS, [])
    )

    research = load_json(RESEARCH, {})
    specs = load_json(SPECS, {})

    source_index = build_url_index(
        research,
        specs,
    )

    missing = [
        product
        for product in products
        if not clean(product.get("image"))
    ]

    if args.limit > 0:
        missing = missing[:args.limit]

    results = []

    safe = 0
    unresolved = 0

    print("=" * 78)
    print("COUPON WORLD IMAGE COVERAGE BATCH v1")
    print("=" * 78)
    print("TOTAL PRODUCTS :", len(products))
    print("MISSING INPUT  :", len(missing))
    print()

    for number, product in enumerate(missing, 1):

        pid = clean(
            product.get("id")
            or product.get("product_id")
        )

        title = clean(
            product.get("title")
        )

        urls = []

        for item in source_index.get(pid, []):
            urls.append(item)

        retail_link = clean(
            product.get("link")
        )

        if (
            retail_link
            and not any(
                token in retail_link.lower()
                for token in BAD_PAGE_TOKENS
            )
        ):
            urls.append(
                {
                    "url": retail_link,
                    "source": "retailer_link",
                }
            )

        unique = []
        seen_pages = set()

        for item in urls:
            source_url = clean(
                item.get("url")
            )

            if (
                not source_url
                or source_url in seen_pages
            ):
                continue

            seen_pages.add(source_url)
            unique.append(item)

        best = None

        for source in unique:

            result = page_candidates(
                title,
                source["url"],
            )

            if not result:
                continue

            result["source_type"] = source["source"]

            if not result.get("images"):
                continue

            if (
                best is None
                or result["identity_score"]
                > best["identity_score"]
            ):
                best = result

        accepted = bool(
            best
            and best.get("images")
            and float(
                best.get("identity_score")
                or 0
            ) >= 0.60
        )

        if accepted:
            safe += 1

            image = best["images"][0]

            status = "CANDIDATE"

            print(
                f"{number:>2} | "
                f"{pid:>2} | "
                f"CANDIDATE | "
                f"score={best['identity_score']:.2f} | "
                f"{title[:55]}"
            )

            print(
                "     ",
                image["source"],
                "|",
                image["url"][:160],
            )

        else:
            unresolved += 1

            status = "UNRESOLVED"

            print(
                f"{number:>2} | "
                f"{pid:>2} | "
                f"UNRESOLVED | "
                f"{title[:65]}"
            )

        results.append(
            {
                "product_id": pid,
                "title": title,
                "status": status,
                "best": best,
            }
        )

    payload = {
        "total_products": len(products),
        "missing_processed": len(missing),
        "candidate_count": safe,
        "unresolved_count": unresolved,
        "results": results,
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print("MISSING PROCESSED :", len(missing))
    print("SAFE CANDIDATES   :", safe)
    print("UNRESOLVED        :", unresolved)
    print("DATABASE          : UNCHANGED")
    print("REPORT            :", OUTPUT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
