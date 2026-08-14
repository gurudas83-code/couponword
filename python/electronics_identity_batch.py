#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, "python")

from resolver_engine import compare_identity
import amazon_search_image_resolver as amazon_search

DB = Path("coupons.json")
OUT = Path("data/electronics_identity_candidates.json")

TARGET_IDS = {
    "24","25","28","31","33","36",
    "41","52","53","54","55",
}

data = json.loads(
    DB.read_text(encoding="utf-8-sig")
)

products = (
    data if isinstance(data, list)
    else data.get("products", [])
)

targets = [
    p for p in products
    if str(p.get("id")) in TARGET_IDS
]

results = []

print("=" * 86)
print("COUPON WORLD ELECTRONICS IDENTITY BATCH v1")
print("=" * 86)
print("TARGETS:", len(targets))
print()

for product in targets:
    pid = str(product.get("id"))
    title = str(product.get("title") or "").strip()
    brand = str(product.get("brand") or "").strip()

    print("-" * 86)
    print(pid, "|", title)

    candidates = amazon_search.search_asins(
        title,
        max_cards=12,
    )

    print("SEARCH CANDIDATES:", len(candidates))

    ranked = []

    for candidate in candidates:
        candidate_title = str(
            candidate.get("search_title") or ""
        ).strip()

        if not candidate_title:
            continue

        decision = compare_identity(
            expected_text=title,
            candidate_title=candidate_title,
            candidate_url=candidate.get("product_url"),
            expected_brand=brand,
        )

        ranked.append({
            "asin": candidate.get("asin"),
            "candidate_title": candidate_title,
            "product_url": candidate.get("product_url"),
            "search_image": candidate.get("search_image"),
            "decision": decision.decision,
            "score": decision.score,
            "reasons": decision.reasons,
        })

    ranked.sort(
        key=lambda x: (
            x["decision"] == "verified",
            x["decision"] == "manual_review",
            x["score"],
        ),
        reverse=True,
    )

    for i, item in enumerate(ranked[:5], 1):
        print(
            i,
            "|",
            item["decision"],
            item["score"],
            "|",
            item["asin"],
            "|",
            item["candidate_title"][:110],
        )

    results.append({
        "product_id": pid,
        "current_title": title,
        "brand": brand,
        "catalog_status": product.get("catalog_status"),
        "candidates": ranked[:12],
    })

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUT.write_text(
    json.dumps(
        {
            "targets": len(targets),
            "results": results,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print()
print("=" * 86)
print("SUMMARY")
print("=" * 86)
print("TARGETS :", len(targets))
print(
    "WITH CANDIDATES :",
    sum(bool(x["candidates"]) for x in results),
)
print(
    "NO CANDIDATES   :",
    sum(not bool(x["candidates"]) for x in results),
)
print("DATABASE        : UNCHANGED")
print("OUTPUT          :", OUT)
