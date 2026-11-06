#!/usr/bin/env python3
"""Fail-closed, standard-library quality checks for the public research artifact.

A green audit means structural contracts pass; it does not certify that every
manufacturer claim, retailer price, or recommendation is independently correct.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

APPROVED_RETAILERS = {
    "amazon": {"www.amazon.in", "amazon.in"},
    "flipkart": {"www.flipkart.com", "flipkart.com"},
    "croma": {"www.croma.com", "croma.com"},
}
BUDGET_CAPS = (10000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000)


def checked_date(value):
    match = re.search(r"20\d\d-\d\d-\d\d", str(value or ""))
    if not match:
        return None
    try:
        return date.fromisoformat(match.group())
    except ValueError:
        return None


def audit(root):
    errors, warnings = [], []
    root = Path(root)

    def require(condition, message):
        if not condition:
            errors.append(message)

    def read_json(rel):
        try:
            return json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"Cannot read {rel}: {exc}")
            return {}

    catalogue = read_json("data/mobile_research_catalogue.json")
    preview = read_json("data/mobile_research_preview.json")
    coupons = read_json("coupons.json")
    cards = catalogue.get("model_cards", [])
    records = catalogue.get("records", [])
    frozen = preview.get("products", [])
    require(len(cards) == 232, f"Model-count contract: expected 232, found {len(cards)}")
    require(len(records) == 235, f"Discovery-count contract: expected 235, found {len(records)}")
    require(len(frozen) == 10, f"Frozen-variant contract: expected 10, found {len(frozen)}")
    require(len({c.get("model_key") for c in cards}) == len(cards), "Duplicate model keys")
    require(len({r.get("record_key") for r in records}) == len(records), "Duplicate discovery keys")
    spec_count = sum(bool(c.get("specifications")) for c in cards)
    field_count = sum(len(c.get("specifications") or {}) for c in cards)
    require(spec_count >= 225, f"Specification coverage dropped below 225: {spec_count}")
    require(field_count >= 2279, f"Specification fields dropped below 2279: {field_count}")

    frozen_ids = sorted(p.get("canonical_product_id") for p in frozen)
    record_ids = sorted(r.get("record_key") for r in records)
    require(
        sorted(k for card in cards for k in card.get("frozen_variant_ids", [])) == frozen_ids,
        "Frozen variants not reconciled to cards",
    )
    require(
        sorted(k for card in cards for k in card.get("discovery_record_keys", [])) == record_ids,
        "Discovery records not reconciled to cards",
    )

    refs = [c for c in cards if c.get("research_budget_reference")]
    require(len(refs) >= 86, f"Dated budget reference coverage dropped below 86: {len(refs)}")
    bands = {}
    now = datetime.now(timezone.utc).date()
    ages = []
    stale_refs = 0
    retailers = Counter()

    for card in cards:
        model = card.get("model_key", "(missing)")
        for field, info in (card.get("specifications") or {}).items():
            if not isinstance(info, dict) or not str(info.get("source_url") or "").startswith("https://"):
                errors.append(f"Unbacked specification {model}/{field}")
        for link in card.get("retailer_search_links") or []:
            store = str(link.get("retailer", "")).lower()
            host = urlsplit(str(link.get("url", ""))).hostname
            retailers[store] += 1
            require(host in APPROVED_RETAILERS.get(store, set()), f"Unapproved {store} research link on {model}")
        ref = card.get("research_budget_reference")
        if not ref:
            continue
        price = ref.get("reference_price_inr")
        require(isinstance(price, (int, float)) and not isinstance(price, bool) and price > 0,
                f"Invalid budget reference price for {model}")
        require(ref.get("live_offer") is False and ref.get("ranking_weight") == 0,
                f"Budget price became a live offer or a ranking signal for {model}")
        require(not re.search(r"OUT.OF.STOCK|UNAVAILABLE|SOLD.OUT|DISCONTINUED",
                              str(ref.get("stock_indication", "")), re.I),
                f"Unbuyable reference admitted for {model}")
        d = checked_date(ref.get("checked_at"))
        if not d:
            errors.append(f"Missing reference check date for {model}")
        else:
            age = (now - d).days
            ages.append(age)
            if age > 30:
                stale_refs += 1

    for store in APPROVED_RETAILERS:
        require(retailers[store] == 232, f"{store} reference-link coverage {retailers[store]}/232")
    for cap in BUDGET_CAPS:
        floor = max(0, cap - (5000 if cap <= 30000 else 10000))
        bands[str(cap)] = sum(floor <= c["research_budget_reference"]["reference_price_inr"] < cap
                              for c in refs if isinstance(c["research_budget_reference"].get("reference_price_inr"), (int, float)))
    require(bands["10000"] >= 1, "Under-10k reference coverage disappeared")
    if stale_refs:
        warnings.append(f"{stale_refs} budget references are older than 30 days; do not claim live pricing")
    if any(str(link.get("url", "")).rstrip("/") == "https://www.croma.com/phones-and-wearables/c/1"
           for c in cards for link in c.get("retailer_search_links") or []):
        warnings.append("Croma links are generic browse-category destinations, not exact-model matches")

    for item in records:
        commerce = item.get("commerce") or {}
        require(not commerce.get("purchase_cta_eligible") and commerce.get("price") is None
                and commerce.get("stock") is None, "Research discovery record wrongly published as a live offer")
    for item in frozen:
        commerce = item.get("commerce") or {}
        require(not commerce.get("purchase_cta_eligible"), "Frozen preview wrongly admits a purchase CTA")
    require(isinstance(coupons, list), "Legacy catalogue is not a JSON array")

    for page in ("index.html", "sitemap.xml", "guides/phone-budget-guides/index.html",
                 "seo/phones-under-10000.html", "seo/phones-under-50000.html"):
        require((root / page).is_file(), f"Public page missing: {page}")
    guide_files = list((root / "seo").glob("*.html"))
    require(len(guide_files) >= 20, "Buying guide HTML pages are missing")

    # Both new categories have only manufacturer research today. Verify the
    # published pages, source links and sitemap but forbid fake merchant schema.
    category_counts, category_fields = {}, 0
    sitemap_text = (root / "sitemap.xml").read_text(encoding="utf-8")
    homepage_text = (root / "index.html").read_text(encoding="utf-8")
    for category in ("accessories", "tvs"):
        hub_path = root / category / "index.html"
        require(hub_path.is_file(), f"Missing research hub /{category}/")
        require(f'href="/{category}/"' in homepage_text, f"No homepage path to /{category}/")
        require(f"https://coupon-world.in/{category}/" in sitemap_text, f"No /{category}/ sitemap entry")
        if not hub_path.is_file():
            continue
        hub_text = hub_path.read_text(encoding="utf-8")
        match = re.search(r'<script type="application/json" id="cr-payload">(.*?)</script>', hub_text, re.S)
        if not match:
            errors.append(f"Missing verifiable research data in /{category}/")
            continue
        try:
            published = json.loads(match.group(1))
        except ValueError:
            errors.append(f"Invalid research-data payload /{category}/")
            continue
        items = published.get("records") or []
        category_counts[category] = len(items)
        require(len(items) >= 4, f"Insufficient published /{category}/ records")
        require(hub_text.count('data-model="') == len(items), f"Unreachable /{category}/ cards")
        for item in items:
            fields = item.get("specifications") or []
            category_fields += len(fields)
            require(len(fields) >= 5 and all(
                str(field.get("source_url") or "").startswith("https://")
                for field in fields
            ), f"Unbacked {category} fields in {item.get('slug')}")
            route = category + "/" + item.get("slug", "") + "/"
            page_file = root / route / "index.html"
            require(page_file.is_file(), f"Missing category research route {route}")
            require("https://coupon-world.in/" + route in sitemap_text, f"Not in sitemap: {route}")
            if not page_file.is_file():
                continue
            page_text = page_file.read_text(encoding="utf-8")
            require(page_text.count("Maker source") >= len(fields), f"Missing per-field sources: {route}")
            require('name="robots" content="index,follow"' in page_text, f"Category page noindex: {route}")
            require('rel="canonical"' in page_text, f"Missing canonical URL: {route}")
            require(not re.search(r'"@type"\s*:\s*"(Product|Offer|AggregateRating)"', page_text),
                    f"Fabricated merchant schema: {route}")
            require(not re.search(r'class="(?:purchase-cta|shop-button)"', page_text),
                    f"Unverified purchase CTA on {route}")
    require(category_counts.get("accessories", 0) >= 4 and category_counts.get("tvs", 0) >= 4,
            "Source-backed category coverage disappeared")

    # Dated workbook research is not a live merchant offer.
    published_workbook_models = {}
    for category, slug in (("tvs","india-20"),("accessories","earbuds-20")):
        hub_path = root / category / slug / "index.html"
        require(hub_path.is_file(), f"Missing 20-product {category} research page")
        if not hub_path.is_file():
            continue
        hub_text = hub_path.read_text(encoding="utf-8")
        require(f"https://coupon-world.in/{category}/{slug}/" in (root / "sitemap.xml").read_text(encoding="utf-8"),
                f"Missing {category} research collection in sitemap")
        require("dated" in hub_text.lower() and "not current offers" in hub_text.lower(),
                f"Missing dated price disclosure on {category} collection")
        require('id="cr-comparison"' in hub_text and 'id="cr-filters"' in hub_text,
                f"Missing comparison/search controls on {category} hub")
        actual=len(list((root / category / slug).glob("*/index.html")))
        published_workbook_models[category] = actual
        require(actual == 20, f"{category} research model count {actual} != 20")
        for item_page in (root / category / slug).glob("*/index.html"):
            html=item_page.read_text(encoding="utf-8")
            route=item_page.relative_to(root).as_posix()
            require('name="robots" content="noindex,follow"' in html,
                    f"Unreviewed workbook detail escaped index gate: {route}")
            require("Amazon, Flipkart and Croma" in html and "Dated quoted reference" in html,
                    f"Missing three-retailer dated comparison: {route}")
            require('"@type":"Offer"' not in html and '"@type": "Offer"' not in html,
                    f"Unsupported Offer structured data: {route}")
            require('class="shop-button"' not in html and 'class="purchase-cta"' not in html,
                    f"Unverified merchant CTA: {route}")

    # Independent industry shipment signals are a separate research intake:
    # do not silently add them to the 232 official catalogue or ranking pool.
    sales_dir = root / "phones" / "india-market-demand-q3-2026"
    market_hub = sales_dir / "index.html"
    require(market_hub.is_file(), "India Q3 2026 market coverage hub missing")
    market_details = list(sales_dir.glob("*/index.html")) if sales_dir.is_dir() else []
    require(len(market_details) == 10, f"Market-signal model research page count {len(market_details)} != 10")
    if market_hub.is_file():
        hub = market_hub.read_text(encoding="utf-8")
        require("NOT an official nationwide Top 10 ranking" in hub,
                "National model-specific rankings falsely asserted")
        require("6 were missing" in hub and "4 already included" in hub,
                "Market audit missing 4-existing / 6-new reconciliation")
        require('href="/phones/india-market-demand-q3-2026/"' in (
            root / "index.html").read_text(encoding="utf-8"),
            "Market coverage has no internal homepage link")
        require("https://coupon-world.in/phones/india-market-demand-q3-2026/" in (
            root / "sitemap.xml").read_text(encoding="utf-8"),
            "Market coverage hub missing from sitemap")
    for detail in market_details:
        content=detail.read_text(encoding="utf-8")
        require('name="robots" content="noindex,follow"' in content,
                f"Unreviewed research detail escaped indexing gate: {detail}")
        require("Manufacturer source" in content and "Omdia India Q3 2026 report" in content,
                f"Research detail missing original evidence: {detail}")
        require('"@type": "Offer"' not in content and 'class="shop-button"' not in content,
                f"Unverified commerce on industry model research page: {detail}")

    result = {
        "result": "PASS" if not errors else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "generated public artifact, not live merchant availability",
        "metrics": {
            "model_cards": len(cards),
            "discovery_records": len(records),
            "frozen_variants": len(frozen),
            "models_with_specs": spec_count,
            "technical_fields": field_count,
            "dated_budget_references": len(refs),
            "max_reference_age_days": max(ages) if ages else None,
            "retailer_search_links": dict(retailers),
            "budget_band_counts": bands,
            "guide_html_files": len(guide_files),
            "source_reviewed_category_models": category_counts,
            "category_documented_fields": category_fields,
            "workbook_category_model_count": published_workbook_models,
            "india_market_sales_model_research_pages": len(market_details),
        },
        "warnings": warnings,
        "errors": errors,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="public", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
