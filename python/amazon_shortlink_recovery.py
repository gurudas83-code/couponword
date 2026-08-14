#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, "python")

from resolver_engine import compare_identity
from amazon_exact_image_recovery import (
    extract_amazon_images,
    choose_best_image,
)

ROOT = Path(".")
DB = ROOT / "coupons.json"
REPORT = ROOT / "data" / "amazon_shortlink_recovery.json"
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


def asin_from_url(url):
    match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})",
        clean(url),
        re.I,
    )

    return match.group(1).upper() if match else ""


def is_amazon_shortlink(url):
    value = clean(url).lower()

    return (
        value.startswith("https://amzn.in/")
        or value.startswith("http://amzn.in/")
        or value.startswith("https://amzn.to/")
        or value.startswith("http://amzn.to/")
    )


def load_database():
    data = json.loads(
        DB.read_text(encoding="utf-8-sig")
    )

    products = (
        data
        if isinstance(data, list)
        else data.get("products", [])
    )

    return data, products


def save_database(data):
    DB.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def backup_database():
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        BACKUP_DIR
        / f"coupons_before_shortlink_recovery_{stamp}.json"
    )

    shutil.copy2(DB, backup)

    return backup


def normalize_exact_url(url, asin):
    if not asin:
        return clean(url)

    return (
        f"https://www.amazon.in/dp/{asin}"
        "?tag=guru0906-21"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Resolve Amazon short links to exact product pages, "
            "verify identity and recover hero images."
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--product-id",
        default="",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
    )

    args = parser.parse_args()

    data, products = load_database()

    targets = []

    for product in products:
        pid = clean(product.get("id"))

        if (
            args.product_id
            and pid != clean(args.product_id)
        ):
            continue

        if clean(product.get("image")):
            continue

        if not is_amazon_shortlink(
            clean(product.get("link"))
        ):
            continue

        targets.append(product)

    if args.limit > 0:
        targets = targets[:args.limit]

    print("=" * 86)
    print("COUPON WORLD AMAZON SHORT-LINK RECOVERY v1")
    print("=" * 86)
    print(
        "MODE    :",
        "WRITE" if args.write else "DRY RUN",
    )
    print("TARGETS :", len(targets))
    print()

    session = requests.Session()

    verified = 0
    image_recovered = 0
    changed = 0
    unresolved = 0

    report_items = []

    backup = None

    if args.write and targets:
        backup = backup_database()

    for index, product in enumerate(
        targets,
        1,
    ):
        pid = clean(product.get("id"))
        title = clean(product.get("title"))
        brand = clean(product.get("brand"))
        short_url = clean(product.get("link"))

        print("-" * 86)
        print(pid, "|", title)
        print("SHORT :", short_url)

        item = {
            "product_id": pid,
            "title": title,
            "short_url": short_url,
            "status": "unresolved",
        }

        try:
            response = session.get(
                short_url,
                headers=HEADERS,
                timeout=(5, 18),
                allow_redirects=True,
            )
        except Exception as error:
            unresolved += 1
            item["error"] = str(error)
            report_items.append(item)

            print(
                "ERROR :",
                str(error)[:180],
            )

            continue

        final_url = clean(response.url)
        asin = asin_from_url(final_url)

        print(
            "HTTP  :",
            response.status_code,
        )
        print(
            "FINAL :",
            final_url,
        )
        print(
            "ASIN  :",
            asin or "NONE",
        )

        item["http_status"] = response.status_code
        item["resolved_url"] = final_url
        item["asin"] = asin

        if response.status_code != 200:
            unresolved += 1
            item["status"] = "http_error"
            report_items.append(item)
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

        print(
            "PAGE  :",
            page_title[:150],
        )

        item["page_title"] = page_title

        identity = compare_identity(
            expected_text=title,
            candidate_title=page_title,
            candidate_url=final_url,
            expected_brand=brand,
        )

        print(
            "MATCH :",
            identity.decision,
            identity.score,
        )

        item["identity_decision"] = (
            identity.decision
        )
        item["identity_score"] = (
            identity.score
        )
        item["identity_reasons"] = (
            identity.reasons
        )

        if identity.decision != "verified":
            unresolved += 1
            item["status"] = "identity_rejected"

            print(
                "WHY   :",
                "; ".join(identity.reasons),
            )

            report_items.append(item)
            continue

        verified += 1

        candidates = extract_amazon_images(
            soup
        )

        best = choose_best_image(
            candidates
        )

        if not best:
            unresolved += 1
            item["status"] = "no_safe_image"
            report_items.append(item)

            print("IMAGE : NONE")
            continue

        image = clean(
            best.get("url")
        )

        image_source = clean(
            best.get("source")
        )

        image_recovered += 1

        print("IMAGE :", image)
        print("SRC   :", image_source)

        exact_url = normalize_exact_url(
            final_url,
            asin,
        )

        item.update(
            {
                "status": "verified",
                "exact_url": exact_url,
                "image": image,
                "image_source": image_source,
            }
        )

        if args.write:
            product["image"] = image

            if asin:
                product["asin"] = asin

            product["link"] = exact_url
            product["linkType"] = "product"

            product["image_provenance"] = {
                "source_type": (
                    "merchant_product_page"
                ),
                "merchant": "amazon.in",
                "source_page": exact_url,
                "verified": True,
                "identity_score": (
                    identity.score
                ),
                "identity_decision": (
                    identity.decision
                ),
                "selection_method": (
                    "amazon_shortlink_exact_hero_v1"
                ),
                "image_source": (
                    image_source
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

        report_items.append(item)

        if (
            args.delay > 0
            and index < len(targets)
        ):
            time.sleep(args.delay)

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(
                    timespec="seconds"
                ),
                "mode": (
                    "write"
                    if args.write
                    else "dry_run"
                ),
                "targets": len(targets),
                "identity_verified": verified,
                "images_recovered": image_recovered,
                "changed": changed,
                "items": report_items,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    if args.write and changed:
        save_database(data)

    print()
    print("=" * 86)
    print("SUMMARY")
    print("=" * 86)
    print(
        "TARGETS           :",
        len(targets),
    )
    print(
        "IDENTITY VERIFIED :",
        verified,
    )
    print(
        "IMAGES RECOVERED  :",
        image_recovered,
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
        (
            "UPDATED"
            if args.write and changed
            else "UNCHANGED"
        ),
    )
    print(
        "REPORT            :",
        REPORT,
    )

    if backup:
        print(
            "BACKUP            :",
            backup,
        )


if __name__ == "__main__":
    raise SystemExit(main())
