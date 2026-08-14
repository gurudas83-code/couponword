#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, "python")
from resolver_engine import compare_identity

ROOT = Path(".")
DB = ROOT / "coupons.json"
BACKUP_DIR = ROOT / ".amazon_image_backups"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def clean(value):
    return str(value or "").strip()


def load_products():
    data = json.loads(
        DB.read_text(encoding="utf-8-sig")
    )

    products = (
        data
        if isinstance(data, list)
        else data.get("products", [])
    )

    return data, products


def save_products(data):
    DB.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def backup_db():
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = (
        BACKUP_DIR
        / f"coupons_before_amazon_image_{stamp}.json"
    )

    path.write_bytes(DB.read_bytes())

    return path


def exact_amazon_product(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()

    return (
        "amazon.in" in host
        and (
            "/dp/" in path
            or "/gp/product/" in path
        )
    )


def add_candidate(
    found,
    value,
    source,
):
    if not value:
        return

    if isinstance(value, dict):
        for url, dimensions in value.items():
            width = None
            height = None

            if (
                isinstance(dimensions, list)
                and len(dimensions) >= 2
            ):
                width = dimensions[0]
                height = dimensions[1]

            add_candidate(
                found,
                {
                    "url": url,
                    "width": width,
                    "height": height,
                },
                source,
            )

        return

    if isinstance(value, list):
        for item in value:
            add_candidate(
                found,
                item,
                source,
            )
        return

    if isinstance(value, dict):
        url = clean(value.get("url"))
        width = value.get("width")
        height = value.get("height")
    else:
        url = clean(value)
        width = None
        height = None

    if not url.startswith(
        ("http://", "https://")
    ):
        return

    lowered = url.lower()

    if any(
        token in lowered
        for token in (
            "sprite",
            "logo",
            "favicon",
            "grey-pixel",
            "transparent-pixel",
        )
    ):
        return

    if any(
        item["url"] == url
        for item in found
    ):
        return

    found.append(
        {
            "url": url,
            "source": source,
            "width": width,
            "height": height,
        }
    )


def extract_amazon_images(soup):
    found = []

    landing = soup.find(
        id="landingImage"
    )

    if landing:
        old_hi = landing.get(
            "data-old-hires"
        )

        if old_hi:
            add_candidate(
                found,
                old_hi,
                "landingImage:data-old-hires",
            )

        dynamic = landing.get(
            "data-a-dynamic-image"
        )

        if dynamic:
            try:
                payload = json.loads(
                    dynamic
                )

                for url, dims in payload.items():
                    found.append(
                        {
                            "url": clean(url),
                            "source": (
                                "landingImage:"
                                "data-a-dynamic-image"
                            ),
                            "width": (
                                dims[0]
                                if isinstance(dims, list)
                                and len(dims) > 0
                                else None
                            ),
                            "height": (
                                dims[1]
                                if isinstance(dims, list)
                                and len(dims) > 1
                                else None
                            ),
                        }
                    )

            except Exception:
                pass

        src = landing.get("src")

        if src:
            add_candidate(
                found,
                src,
                "landingImage:src",
            )

    return found


def rank_image(candidate):
    url = clean(
        candidate.get("url")
    )

    score = 0

    width = candidate.get("width")
    height = candidate.get("height")

    if (
        isinstance(width, int)
        and isinstance(height, int)
    ):
        score += min(
            width * height / 100000,
            30,
        )

    if "_SL1500_" in url:
        score += 50

    if "_SL1200_" in url:
        score += 45

    if "_SL1000_" in url:
        score += 40

    if "_SX" in url:
        score -= 5

    if (
        candidate.get("source")
        == "landingImage:data-old-hires"
    ):
        score += 25

    return score


def choose_best_image(images):
    valid = [
        item
        for item in images
        if clean(item.get("url"))
    ]

    if not valid:
        return None

    valid.sort(
        key=rank_image,
        reverse=True,
    )

    return valid[0]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
    )

    parser.add_argument(
        "--force",
        action="store_true",
    )

    parser.add_argument(
        "--product-id",
        default="",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    args = parser.parse_args()

    data, products = load_products()

    targets = []

    for product in products:
        pid = clean(product.get("id"))

        if (
            args.product_id
            and pid != clean(args.product_id)
        ):
            continue

        link = clean(
            product.get("link")
        )

        if not exact_amazon_product(link):
            continue

        if (
            clean(product.get("image"))
            and not args.force
        ):
            continue

        targets.append(product)

    if args.limit > 0:
        targets = targets[:args.limit]

    print("=" * 82)
    print(
        "COUPON WORLD AMAZON EXACT IMAGE RECOVERY v1"
    )
    print("=" * 82)
    print(
        "MODE    :",
        "WRITE"
        if args.write
        else "DRY RUN",
    )
    print("TARGETS :", len(targets))
    print()

    changed = 0
    verified = 0
    unresolved = 0

    backup_path = None

    if args.write and targets:
        backup_path = backup_db()

    for product in targets:
        pid = clean(product.get("id"))
        title = clean(product.get("title"))
        brand = clean(product.get("brand"))
        url = clean(product.get("link"))

        print("-" * 82)
        print(pid, "|", title)

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=(5, 18),
                allow_redirects=True,
            )
        except Exception as error:
            unresolved += 1
            print(
                "ERROR    :",
                str(error)[:180],
            )
            continue

        print(
            "HTTP     :",
            response.status_code,
        )

        if response.status_code != 200:
            unresolved += 1
            continue

        soup = BeautifulSoup(
            response.text,
            "lxml",
        )

        page_title = clean(
            soup.title.get_text(
                " ",
                strip=True,
            )
            if soup.title
            else ""
        )

        identity = compare_identity(
            expected_text=title,
            candidate_title=page_title,
            candidate_url=response.url,
            expected_brand=brand,
        )

        print(
            "IDENTITY :",
            identity.decision,
            identity.score,
        )

        if (
            identity.decision
            != "verified"
        ):
            unresolved += 1
            print(
                "ACTION   : SKIP "
                "(identity not verified)"
            )
            continue

        verified += 1

        images = extract_amazon_images(
            soup
        )

        best = choose_best_image(
            images
        )

        if not best:
            unresolved += 1
            print("IMAGE    : NONE")
            continue

        print(
            "IMAGE    :",
            best["url"],
        )
        print(
            "SOURCE   :",
            best["source"],
        )

        if args.write:
            product["image"] = best["url"]

            product["image_provenance"] = {
                "source_type": (
                    "merchant_product_page"
                ),
                "merchant": "amazon.in",
                "source_page": response.url,
                "verified": True,
                "identity_score": (
                    identity.score
                ),
                "identity_decision": (
                    identity.decision
                ),
                "selection_method": (
                    "amazon_exact_page_hero_v1"
                ),
                "image_source": (
                    best["source"]
                ),
                "width": (
                    best.get("width")
                ),
                "height": (
                    best.get("height")
                ),
                "verified_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat(
                        timespec="seconds"
                    )
                ),
            }

            changed += 1

    if args.write and changed:
        save_products(data)

    print()
    print("=" * 82)
    print("SUMMARY")
    print("=" * 82)
    print(
        "IDENTITY VERIFIED :",
        verified,
    )
    print(
        "UNRESOLVED        :",
        unresolved,
    )
    print(
        "CHANGED           :",
        changed,
    )
    print(
        "DATABASE          :",
        "UPDATED"
        if args.write and changed
        else "UNCHANGED",
    )

    if backup_path:
        print(
            "BACKUP            :",
            backup_path,
        )


if __name__ == "__main__":
    main()
