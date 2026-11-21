#!/usr/bin/env python3
"""Review-first exact-SKU API check for Coupon World Top50 (manual opt-in).

Usage:
    python scripts/verify_top50_affiliate.py --queue public/data/top50_sku_research_queue.json
    python scripts/verify_top50_affiliate.py --queue public/data/top50_sku_research_queue.json --live --limit 10

For live calls, add reviewed mappings in data/top50_retailer_identity_review.json.
Never put credentials or unreviewed provider results in the public artifact.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from top50_affiliate_checks import amazon_get_item, flipkart_get_product, configured


def audit(queue: dict, reviews: dict, *, live: bool = False, limit: int = 10) -> dict:
    if queue.get("mode") != "TOP50_HISTORICAL_DEMAND_RESEARCH_QUEUE_NOT_LIVE_OFFERS":
        raise ValueError("Unexpected Top50 queue version")
    candidates = queue.get("products") or []
    if len(candidates) != 50 or len({row["model_key"] for row in candidates}) != 50:
        raise ValueError("Top50 must contain exactly 50 unique existing models")
    if reviews.get("mode") != "REVIEWED_TOP50_VARIANT_TO_RETAILER_SKU":
        raise ValueError("Unexpected human-review mapping schema")
    by_model = {row["model_key"]: row for row in candidates}
    mapping = reviews.get("records") or []
    if len(mapping) != len({(row.get("model_key"), row.get("retailer")) for row in mapping}):
        raise ValueError("Duplicate retailer mapping for a model")
    results = []
    outbound = 0
    for row in mapping:
        model = by_model.get(row.get("model_key"))
        if model is None:
            raise ValueError("Reviewer mapping references a phone outside Top50")
        retailer = str(row.get("retailer") or "").lower()
        if retailer not in {"amazon", "flipkart"}:
            raise ValueError("Only Amazon or Flipkart supported")
        exact_id = str(row.get("retailer_product_id") or "").upper()
        if retailer == "amazon" and not re.fullmatch(r"[A-Z0-9]{10}", exact_id):
            raise ValueError("Invalid reviewed Amazon ASIN")
        if retailer == "flipkart" and not re.fullmatch(r"[A-Z0-9]{10,32}", exact_id):
            raise ValueError("Invalid reviewed Flipkart PID")
        if row.get("variant") != model["variant_to_check"]:
            raise ValueError("Retailer mapping must match the requested exact memory variant")
        if row.get("review_status") != "APPROVED" or not str(row.get("manufacturer_source_url") or "").startswith("https://"):
            raise ValueError("Exact SKU mappings must be explicitly approved against a manufacturer source")
        # The operator's explicit authorization grants *read-only* provider
        # observations; each result remains subject to the existing offer gate.
        record = {"model_key": model["model_key"], "variant": row["variant"],
                  "retailer": retailer, "retailer_product_id": exact_id,
                  "publishable": False}
        if not live:
            record["status"] = "READY_FOR_MANUAL_API_CHECK" if configured(retailer) else "MISSING_API_CREDENTIALS"
        elif not configured(retailer):
            record["status"] = "MISSING_API_CREDENTIALS"
        elif outbound >= limit:
            record["status"] = "BATCH_LIMIT_REACHED"
        else:
            outbound += 1
            try:
                evidence = (amazon_get_item(exact_id) if retailer == "amazon" else flipkart_get_product(exact_id))
                record.update(evidence)
                record["publishable"] = False
            except Exception:
                # Errors are deliberately not printed: some HTTP provider errors
                # echo credential-bearing headers or query parameters.
                record["status"] = "PROVIDER_REQUEST_FAILED"
        results.append(record)
    mapped = {r["model_key"] for r in results}
    return {
        "mode": "TOP50_PRIVATE_REVIEW_ONLY_NO_PUBLIC_PRICE",
        "candidate_models": len(candidates),
        "reviewed_model_count": len(mapped),
        "unmapped_model_count": len(candidates) - len(mapped),
        "approved_retailer_mappings": len(mapping),
        "live_provider_requests": outbound,
        "results": results,
        "notice": "Raw private evidence only. Never copy this file to public assets or into the verified-offer store without exact variant, source, current price and stock gates.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", type=Path, default=ROOT / "public/data/top50_sku_research_queue.json")
    ap.add_argument("--reviews", type=Path, default=ROOT / "data/top50_retailer_identity_review.json")
    ap.add_argument("--out", type=Path, default=ROOT / "reports/top50_affiliate_private_review.json")
    ap.add_argument("--live", action="store_true", help="Explicitly authorize limited external provider reads")
    ap.add_argument("--limit", type=int, default=10, help="Maximum provider calls, 1-50")
    args = ap.parse_args()
    if not 1 <= args.limit <= 50:
        ap.error("--limit must be between 1 and 50")
    if args.live and "public" in args.out.resolve().parts:
        ap.error("Private raw observations must not be written into public artifact")
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    result = audit(queue, reviews, live=args.live, limit=args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Top50 research candidates:", result["candidate_models"])
    print("Human-reviewed distinct models:", result["reviewed_model_count"])
    print("Provider requests:", result["live_provider_requests"])
    print("Private report:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
