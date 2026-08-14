#!/usr/bin/env python3

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "python")

import amazon_search_image_resolver as resolver

DB = Path("coupons.json")
CACHE = Path("data/amazon_search_candidate_cache.json")

SPECIFIC_IDS = {
    "30",  # OnePlus Nord CE
    "34",  # Fire TV Stick 4K
    "37",  # Mi Power Bank 10000mAh
    "39",  # Kindle Paperwhite
    "42",  # Realme Buds T100
    "58",  # JBL Tune 510BT
    "60",  # Typecase keyboard case
    "62",  # Hauser pen
    "64",  # Chair bush
    "66",  # UGAOO plants
    "69",  # Redmi Note 13 5G
}

data = json.loads(
    DB.read_text(encoding="utf-8-sig")
)

products = (
    data if isinstance(data, list)
    else data.get("products", [])
)

if CACHE.exists():
    cache = json.loads(
        CACHE.read_text(encoding="utf-8")
    )
else:
    cache = {}

targets = [
    p for p in products
    if (
        str(p.get("id")) in SPECIFIC_IDS
        and not str(p.get("image") or "").strip()
    )
]

print("=" * 78)
print("AMAZON SEARCH CANDIDATE CACHE BUILDER")
print("=" * 78)
print("TARGETS:", len(targets))
print()

new_hits = 0
cached_hits = 0
zero = 0

for index, product in enumerate(targets, 1):
    pid = str(product.get("id"))
    title = str(product.get("title") or "").strip()

    print("-" * 78)
    print(f"[{index}/{len(targets)}] {pid} | {title}")

    existing = cache.get(pid, {})

    if existing.get("candidates"):
        print(
            "CACHE   :",
            len(existing["candidates"]),
            "candidate(s)"
        )
        cached_hits += 1
        continue

    candidates = resolver.search_asins(
        title,
        max_cards=12,
    )

    if candidates:
        cache[pid] = {
            "title": title,
            "candidates": candidates,
        }

        new_hits += 1

        print(
            "FOUND   :",
            len(candidates),
        )

        for item in candidates[:3]:
            print(
                " ",
                item.get("asin"),
                "|",
                str(item.get("search_title") or "")[:100],
            )
    else:
        zero += 1
        print("FOUND   : 0")

    CACHE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    CACHE.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    if index < len(targets):
        wait = random.uniform(8, 12)
        print(f"WAIT    : {wait:.1f}s")
        time.sleep(wait)

print()
print("=" * 78)
print("SUMMARY")
print("=" * 78)
print("TARGETS       :", len(targets))
print("NEW HITS      :", new_hits)
print("CACHED HITS   :", cached_hits)
print("ZERO RESULTS  :", zero)
print("CACHE         :", CACHE)
print("DATABASE      : UNCHANGED")
