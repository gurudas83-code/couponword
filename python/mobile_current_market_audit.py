#!/usr/bin/env python3
"""Find current, evidence-backed mobile candidates for a budget gap.

Read-only: produces a review manifest and never mutates catalogs or registries.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "mobile_current_market_audit.json"
DEFAULT_BRANDS = ("Samsung", "Lava", "Infinix", "realme", "POCO")


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_price(value: Any) -> float | None:
    match = re.search(r"([\d,]+(?:\.\d{1,2})?)", clean(value))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def audit_brand(brand: str, budget: int, max_cards: int) -> list[dict[str, Any]]:
    from amazon_search_image_resolver import search_asins
    from promote_mobile_canonical import fetch_amazon_identity
    from resolver_engine import candidate_is_product_imposter, parse_identity

    query = f"{brand} smartphone under {budget}"
    rows: list[dict[str, Any]] = []
    try:
        cards = search_asins(query, max_cards=max_cards)
    except Exception as error:
        return [{"brand_query": brand, "status": "SEARCH_FAILED", "reason": str(error)}]

    for card in cards:
        asin = clean(card.get("asin")).upper()
        title = clean(card.get("search_title"))
        price = parse_price(card.get("search_price_text"))
        method = clean(card.get("search_price_evidence_method"))
        row: dict[str, Any] = {
            "brand_query": brand, "asin": asin, "title": title,
            "price": price, "price_evidence_method": method,
            "status": "BLOCKED", "reason": "",
        }

        if not asin or not title:
            row["reason"] = "missing exact ASIN or search-card title"
            rows.append(row)
            continue
        if price is None or price <= 0 or price > budget:
            row["reason"] = "verified search-card price is missing or outside budget"
            rows.append(row)
            continue
        if method not in {
            "amazon_exact_asin_search_card",
            "amazon_exact_asin_search_card_offer_text",
        }:
            row["reason"] = "price is not exact-ASIN search-card evidence"
            rows.append(row)
            continue

        imposter, imposter_reason = candidate_is_product_imposter(
            "smartphone handset", title
        )
        if imposter:
            row["reason"] = imposter_reason
            rows.append(row)
            continue

        normalized_title = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
        normalized_brand = re.sub(r"[^a-z0-9]+", " ", brand.lower()).strip()

        if re.search(
            r"\b(?:keypad|feature phone|protection plan|insurance plan|"
            r"extended warranty|power bank|case|cover|protector|"
            r"screen guard|tempered glass|cable)\b",
            normalized_title,
            re.I,
        ):
            row["reason"] = "candidate is not a smartphone handset"
            rows.append(row)
            continue

        handset_signal = bool(re.search(
            r"\b(?:smartphone|galaxy|iphone|redmi|poco|realme|infinix|"
            r"lava|motorola|moto|oppo|vivo|iqoo|oneplus|nothing|pixel)\b",
            normalized_title,
            re.I,
        ))
        if not handset_signal:
            row["reason"] = "smartphone handset identity is not explicit"
            rows.append(row)
            continue

        parsed = parse_identity(title)
        parsed_brand = clean(parsed.brand)

        # If the retailer title explicitly identifies another brand, fail closed.
        # Some genuine OEM listings omit the brand and use a protected family
        # identity such as "Galaxy M17". In that case, retain the requested
        # brand as context and let the existing exact-page strict identity gate
        # make the final decision.
        if (
            parsed_brand
            and parsed_brand.casefold() != brand.casefold()
        ):
            row["reason"] = "parsed candidate brand does not match requested brand"
            rows.append(row)
            continue

        identity_brand = parsed_brand or brand

        brand_explicit = bool(
            re.search(
                rf"(?:^|\s){re.escape(normalized_brand)}(?:\s|$)",
                normalized_title,
            )
        )

        expected_identity_text = (
            title
            if brand_explicit
            else f"{brand} {title}".strip()
        )

        try:
            live = fetch_amazon_identity(
                asin,
                expected_identity_text,
                identity_brand,
            )
        except BaseException as error:
            row["reason"] = str(error)
            rows.append(row)
            continue

        row.update({
            "status": "VERIFIED_FOR_REPLACEMENT_REVIEW",
            "reason": "exact search-card price and exact ASIN page identity verified",
            "brand": identity_brand,
            "model_tokens": parsed.model_tokens,
            "ram_tokens": parsed.ram_tokens,
            "storage_tokens": parsed.storage_tokens,
            "amazon_url": f"https://www.amazon.in/dp/{asin}",
            "page_title": live.get("page_title"),
            "identity_score": live.get("resolver_score"),
        })
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=10000)
    parser.add_argument("--brands", default=",".join(DEFAULT_BRANDS))
    parser.add_argument("--max-cards", type=int, default=12)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    brands = [clean(x) for x in args.brands.split(",") if clean(x)]
    print("COUPON WORLD - CURRENT MOBILE MARKET AUDIT")
    print("Mode          :", "LIVE READ-ONLY" if args.live else "PLAN ONLY")
    print("Budget        :", args.budget)
    print("Brands        :", ", ".join(brands))
    print("Database write: NO")
    if not args.live:
        for brand in brands:
            print("PLAN |", f"{brand} smartphone under {args.budget}")
        return 0

    results: list[dict[str, Any]] = []
    seen_asins: set[str] = set()
    for brand in brands:
        for row in audit_brand(brand, args.budget, max(1, min(args.max_cards, 24))):
            asin = clean(row.get("asin"))
            if asin and asin in seen_asins:
                continue
            if asin:
                seen_asins.add(asin)
            results.append(row)
            print(row.get("status"), "|", brand, "|", asin or "NO-ASIN", "|", row.get("title", ""))

    verified = [x for x in results if x.get("status") == "VERIFIED_FOR_REPLACEMENT_REVIEW"]
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_read_only",
        "database_write": False,
        "budget": args.budget,
        "brands": brands,
        "counts": {"reviewed": len(results), "verified_for_review": len(verified)},
        "verified_candidates": verified,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Output        :", args.output)
    print("Reviewed      :", len(results))
    print("Verified      :", len(verified))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
