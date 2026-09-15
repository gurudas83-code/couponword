#!/usr/bin/env python3
"""Audit priority mobile identities against exact live Amazon evidence.

This utility is deliberately read-only. It never creates canonical IDs and
never writes either the retailer registry or mobile intelligence repository.
Verified output is an approval manifest for a later durable catalog migration.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UNIVERSE = ROOT / "data" / "mobile_universe_priority_126.json"
DEFAULT_OUTPUT = ROOT / "data" / "mobile_priority_identity_audit.json"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_products(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    products = payload.get("products") if isinstance(payload, dict) else None
    if not isinstance(products, list):
        raise SystemExit("BLOCKED: priority universe products list is missing")
    return [row for row in products if isinstance(row, dict)]


def expected_title(row: dict[str, Any]) -> str:
    return clean(" ".join(filter(None, (
        clean(row.get("brand")), clean(row.get("model")), clean(row.get("variant")),
    ))))


def search_card_url(card: dict[str, Any]) -> str:
    asin = clean(card.get("asin")).upper()
    return clean(card.get("product_url")) or (
        f"https://www.amazon.in/dp/{asin}" if asin else ""
    )


def audit_one(row: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    from amazon_search_image_resolver import search_asins
    from mobile_exact_identity_gate import AUTO_REUSE, classify_mobile_identity_reuse
    from promote_mobile_canonical import fetch_amazon_identity, find_asin_owners

    title = expected_title(row)
    brand = clean(row.get("brand"))
    result: dict[str, Any] = {
        "priority": row.get("priority"), "brand": brand,
        "model": clean(row.get("model")), "variant": clean(row.get("variant")),
        "budget_bucket": clean(row.get("budget_bucket")),
        "expected_title": title, "status": "NO_VERIFIED_MATCH",
        "verified_mapping": None, "candidates_reviewed": [],
    }

    try:
        cards = search_asins(title, max_cards=12)
    except Exception as error:
        result["status"] = "SEARCH_FAILED"
        result["reason"] = str(error)
        return result

    for card in cards:
        asin = clean(card.get("asin")).upper()
        candidate_title = clean(card.get("search_title"))
        url = search_card_url(card)
        gate = classify_mobile_identity_reuse(
            expected_text=title,
            candidate_title=candidate_title,
            candidate_url=url,
            expected_brand=brand,
        )
        review = {
            "asin": asin, "title": candidate_title,
            "gate_status": gate.get("status"), "gate_reason": gate.get("reason"),
        }
        result["candidates_reviewed"].append(review)
        if not asin or gate.get("status") != AUTO_REUSE:
            continue

        try:
            live = fetch_amazon_identity(asin, title, brand)
        except BaseException as error:
            review["page_status"] = "BLOCKED"
            review["page_reason"] = str(error)
            continue

        owners = find_asin_owners(registry, asin)
        if owners:
            result["status"] = "ASIN_ALREADY_OWNED"
            result["reason"] = f"ASIN already registered to {owners}"
            result["verified_mapping"] = {"asin": asin, "owners": owners}
            return result

        result["status"] = "VERIFIED_FOR_CATALOG_REVIEW"
        result["verified_mapping"] = {
            "asin": asin,
            "amazon_url": f"https://www.amazon.in/dp/{asin}",
            "page_title": live.get("page_title"),
            "identity_score": live.get("resolver_score"),
            "strict_status": live.get("strict_status"),
            "source": "amazon_exact_page+mobile_exact_identity_gate_v1",
        }
        return result

    if not cards:
        result["reason"] = "Amazon search returned no product cards"
    else:
        result["reason"] = "No search card and exact page passed the strict identity gate"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--budget-bucket", default="<10k")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    selected = [
        row for row in load_products(args.universe)
        if not args.budget_bucket
        or clean(row.get("budget_bucket")).casefold() == args.budget_bucket.casefold()
    ][:max(1, min(args.limit, 126))]

    print("COUPON WORLD - PRIORITY MOBILE IDENTITY AUDIT")
    print("Mode          :", "LIVE READ-ONLY" if args.live else "PLAN ONLY")
    print("Budget bucket :", args.budget_bucket or "ALL")
    print("Records       :", len(selected))
    print("Database write: NO")

    if not args.live:
        for row in selected:
            print(f"PLAN | {row.get('priority')} | {expected_title(row)}")
        print("Run with --live to produce a verified identity review manifest.")
        return 0

    from retailer_product_registry import load_registry

    registry = load_registry()
    results = []
    for row in selected:
        item = audit_one(row, registry)
        results.append(item)
        mapping = item.get("verified_mapping") or {}
        print(
            f"{item['status']} | {item['priority']} | {item['expected_title']}"
            + (f" | {mapping.get('asin')}" if mapping.get("asin") else "")
        )

    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1

    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_read_only",
        "database_write": False,
        "budget_bucket": args.budget_bucket,
        "counts": {"total": len(results), **counts},
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Output        :", args.output)
    print("Summary       :", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
