#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, quote_plus

import re
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, "python")
from resolver_engine import compare_identity

ROOT = Path(".")
DB = ROOT / "coupons.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

AFFILIATE_TAG = "guru0906-21"


def clean(v):
    return str(v or "").strip()


def is_amazon_search(url):
    try:
        p = urlparse(url)
    except Exception:
        return False

    return (
        "amazon.in" in (p.hostname or "").lower()
        and p.path.rstrip("/") == "/s"
    )


def search_asins(title, max_cards=12):
    """
    Search Amazon using a fresh clean title query.

    Do not reuse historical affiliate/search URLs because long encoded
    queries and stale parameters can reduce result reliability.
    """

    query = clean(title)

    if not query:
        return []

    url = (
        "https://www.amazon.in/s?k="
        + quote_plus(query)
    )

    session = requests.Session()

    headers = dict(HEADERS)
    headers.update(
        {
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,*/*;q=0.8"
            ),
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )

    for attempt in range(2):
        try:
            r = session.get(
                url,
                headers=headers,
                timeout=(5, 18),
                allow_redirects=True,
            )
        except Exception:
            continue

        if r.status_code != 200:
            continue

        soup = BeautifulSoup(
            r.text,
            "lxml",
        )

        cards = soup.select(
            'div[data-component-type="s-search-result"][data-asin]'
        )

        if not cards:
            continue

        results = []

        for card in cards:
            asin = clean(
                card.get("data-asin")
            )

            if not asin:
                continue

            title_text = ""

            # Amazon changes title markup frequently.
            for selector in (
                "h2 a span",
                "h2 span",
                "[data-cy='title-recipe'] span",
                "a.a-link-normal.s-line-clamp-2 span",
                "a.a-link-normal.s-line-clamp-4 span",
            ):
                nodes = card.select(selector)

                for node in nodes:
                    candidate = clean(
                        node.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    if len(candidate) > len(title_text):
                        title_text = candidate

            image_node = card.select_one(
                "img.s-image"
            )

            search_image = (
                clean(image_node.get("src"))
                if image_node
                else ""
            )

            image_alt = (
                clean(image_node.get("alt"))
                if image_node
                else ""
            )

            if len(image_alt) > len(title_text):
                title_text = image_alt

            # Capture the primary payable price from this exact ASIN-bound
            # Amazon search-result card. This remains discovery evidence
            # until downstream price validation accepts it.
            search_price_text = ""

            for selector in (
                ".a-price:not(.a-text-price) .a-offscreen",
                "[data-a-color='price'] .a-offscreen",
                ".a-price .a-offscreen",
            ):
                for price_node in card.select(selector):
                    candidate_price = clean(
                        price_node.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    if candidate_price:
                        search_price_text = candidate_price
                        break

                if search_price_text:
                    break
            # Fallback for Amazon cards where price is visible only
            # in the exact ASIN-bound card text.
            search_price_evidence_method = ""

            if not search_price_text:
                card_text = clean(
                    card.get_text(
                        " ",
                        strip=True,
                    )
                )

                price_match = re.search(
                    r"₹\s*([\d,]+(?:\.\d{1,2})?)"
                    r"\s*\(\s*\d+\s+new\s+offers?\s*\)",
                    card_text,
                    re.I,
                )

                if price_match:
                    search_price_text = (
                        "₹" + price_match.group(1)
                    )

                    search_price_evidence_method = (
                        "amazon_exact_asin_search_card_offer_text"
                    )
            else:
                search_price_evidence_method = (
                    "amazon_exact_asin_search_card"
                )


            results.append(
                {
                    "asin": asin,
                    "search_title": title_text,
                    "search_image": search_image,
                    "search_price_text": search_price_text,
                    "search_price_currency": (
                        "INR"
                        if search_price_text
                        else ""
                    ),
                    "search_price_evidence_method": (
                        search_price_evidence_method
                    ),
                    "product_url": (
                        f"https://www.amazon.in/dp/{asin}"
                        f"?tag={AFFILIATE_TAG}"
                    ),
                    "search_url": url,
                }
            )

            if len(results) >= max_cards:
                break

        if results:
            return results

    return []


def amazon_detail(url):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=(5, 18),
            allow_redirects=True,
        )
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }

    if r.status_code != 200:
        return {
            "ok": False,
            "status": r.status_code,
        }

    soup = BeautifulSoup(r.text, "lxml")

    title = clean(
        soup.title.get_text(" ", strip=True)
        if soup.title else ""
    )

    landing = soup.find(id="landingImage")

    image = ""
    source = ""

    if landing:
        image = clean(
            landing.get("data-old-hires")
        )

        if image:
            source = "landingImage:data-old-hires"

        if not image:
            dynamic = clean(
                landing.get("data-a-dynamic-image")
            )

            if dynamic:
                try:
                    payload = json.loads(dynamic)

                    if payload:
                        image = max(
                            payload,
                            key=lambda u: (
                                payload[u][0] * payload[u][1]
                                if isinstance(payload[u], list)
                                and len(payload[u]) >= 2
                                else 0
                            ),
                        )

                        source = (
                            "landingImage:"
                            "data-a-dynamic-image"
                        )
                except Exception:
                    pass

        if not image:
            image = clean(
                landing.get("src")
            )

            if image:
                source = "landingImage:src"

    return {
        "ok": True,
        "title": title,
        "image": image,
        "image_source": source,
        "final_url": r.url,
    }


def title_is_specific_enough(title: str) -> bool:
    """
    Auto-resolution is allowed only when the catalogue title carries
    meaningful model/variant identity.

    Generic titles such as "HP Wireless Mouse" or "Sony Wireless
    Headphones" must not silently resolve to an arbitrary current model.
    """

    value = clean(title).lower()

    generic_exact = {
        "sony wireless headphones",
        "hp wireless mouse",
        "philips trimmer",
        "milton thermosteel bottle",
        "american tourister trolley bag",
        "asus gaming laptop",
        "titan analog watch",
        "wildcraft backpack 35l",
        "levi's men's jeans",
        "strauss yoga mat",
        "mamaearth skincare combo",
        "kore adjustable dumbbells",
        "cello water bottle set",
        "bajaj ceiling fan",
        "apple airpods",
        "dell inspiron laptop",
        "prestige induction cooktop",
        "lakme makeup kit",
        "samsung 28l microwave oven",
        "samsung 25l microwave oven",
        "puma men's running shoes",
        "boat stone bluetooth speaker",
        "boult audio bluetooth speaker",
        "noise colorfit smartwatch",
    }

    if value in generic_exact:
        return False

    # Model identity usually contains digits/codes or a sufficiently
    # specific named product family.
    has_digit = any(ch.isdigit() for ch in value)

    strong_names = (
        "echo dot",
        "fire tv stick",
        "kindle paperwhite",
        "airdopes 311",
        "rockerz 450",
        "tune 510bt",
        "redmi note 13",
        "nord ce",
        "galaxy m16",
        "galaxy m36",
        "buds t100",
        "power bank 10000mah",
    )

    return has_digit or any(name in value for name in strong_names)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--cards",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    data = json.loads(
        DB.read_text(encoding="utf-8-sig")
    )

    products = (
        data
        if isinstance(data, list)
        else data.get("products", [])
    )

    targets = [
        p for p in products
        if (
            not clean(p.get("image"))
            and is_amazon_search(
                clean(p.get("link"))
            )
        )
    ]

    if args.limit:
        targets = targets[:args.limit]

    print("=" * 84)
    print("AMAZON SEARCH -> EXACT PRODUCT IMAGE RESOLVER v1")
    print("=" * 84)
    print("TARGETS:", len(targets))
    print()

    resolved = 0
    unresolved = 0

    for p in targets:

        pid = clean(p.get("id"))
        title = clean(p.get("title"))
        brand = clean(p.get("brand"))
        search_url = clean(p.get("link"))

        print("-" * 84)
        print(pid, "|", title)

        if not title_is_specific_enough(title):
            unresolved += 1
            print("RESULT : SKIPPED_GENERIC")
            print("REASON : Catalogue title lacks exact model identity")
            continue

        candidates = search_asins(
            title,
            max_cards=args.cards,
        )

        print(
            "SEARCH CANDIDATES:",
            len(candidates),
        )

        winner = None

        for number, candidate in enumerate(
            candidates,
            1,
        ):
            search_title = clean(
                candidate.get("search_title")
            )

            if not search_title:
                continue

            card_decision = compare_identity(
                expected_text=title,
                candidate_title=search_title,
                candidate_url=candidate["product_url"],
                expected_brand=brand,
            )

            print(
                f"  {number:>2} |",
                candidate["asin"],
                "| CARD",
                card_decision.decision,
                card_decision.score,
                "|",
                search_title[:85],
            )

            if card_decision.decision != "verified":
                continue

            # Only now fetch the exact ASIN detail page.
            detail = amazon_detail(
                candidate["product_url"]
            )

            if not detail.get("ok"):
                continue

            image = clean(
                detail.get("image")
            )

            if not image:
                continue

            winner = {
                **candidate,
                **detail,
                "identity_score": card_decision.score,
                "identity_source": "amazon_search_card",
            }

            break

        if winner:
            resolved += 1

            print("RESULT : VERIFIED")
            print("ASIN   :", winner["asin"])
            print("URL    :", winner["product_url"])
            print("IMAGE  :", winner["image"])
            print(
                "SOURCE :",
                winner["image_source"],
            )

        else:
            unresolved += 1
            print("RESULT : UNRESOLVED")

    print()
    print("=" * 84)
    print("SUMMARY")
    print("=" * 84)
    print("RESOLVED  :", resolved)
    print("UNRESOLVED:", unresolved)
    print("DATABASE  : UNCHANGED")


if __name__ == "__main__":
    main()
