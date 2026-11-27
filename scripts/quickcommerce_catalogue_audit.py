#!/usr/bin/env python3
"""Bounded, opt-in provider observations. Never writes public catalogue/offers.

Model searches are candidate discovery, NOT exact canonical-variant verification.
Images remain references pending rights and visual review. No retries or schedules.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector, SOURCE, _tokens, _positive_price, _listing_model_name


def load_targets(category="all"):
    mobile = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig"))
    other = json.loads((ROOT / "data/india_tv_earbuds_40_catalogue.json").read_text(encoding="utf-8-sig"))
    rows = [dict(row, audit_id=row["model_key"], category="mobiles") for row in mobile["model_cards"]]
    rows += [dict(row, audit_id=row["id"], category="tvs" if row["category"] == "tvs" else "earbuds") for row in other["records"]]
    return [row for row in rows if category == "all" or row["category"] == category]


def query_for(row):
    brand, model = str(row["brand"]).strip(), str(row["model"]).strip()
    # Retailer search treats the parentheses in names such as "Phone (3a)"
    # inconsistently. Keep the canonical model identity unchanged, but send a
    # provider-friendly search phrase so the exact listing gate can inspect the
    # returned SKU instead of failing before identity validation.
    model = re.sub(r"[()]", "", model)
    return model if _tokens(model).startswith(_tokens(brand) + " ") else f"{brand} {model}"


def listing_candidate(item, row):
    """Conservative candidate identity; no fuzzy or cheapest-price selection."""
    if not isinstance(item, dict):
        return False
    pid = str(item.get("id") or "")
    url = urlsplit(str(item.get("deeplink") or ""))
    if (not re.fullmatch(r"[A-Z0-9]{12,24}", pid) or url.scheme != "https"
            or url.hostname not in {"flipkart.com", "www.flipkart.com"}
            or url.username or url.password or url.port not in {None, 443}
            or "/p/" not in url.path or parse_qs(url.query).get("pid") != [pid]):
        return False
    title = str(item.get("name") or "")
    expected = _tokens(query_for(row))
    candidate_model = _tokens(_listing_model_name(title))
    # A few Indian catalogue records omit the radio variant from the model
    # key (for example `Infinix GT 30 Pro`), while Flipkart titles publish the
    # same handset as `Infinix GT 30 Pro 5G`. Treat only that trailing network
    # suffix as a display-name alias; the brand, model stem, SKU and physical
    # configuration gates remain strict.
    # Storage-specific catalogue cards must state the requested capacity too.
    storage = re.search(r"\\s+(\\d+)\\s*(GB|TB)$", expected, re.I)
    if row["category"] == "mobiles":
        # Require the provider's brand field as well as the title. A wrong-brand
        # item can otherwise pass when its display title repeats the target name.
        if _tokens(item.get("brand")) != _tokens(row["brand"]):
            return False
        model_expected = expected
        if storage:
            model_expected = expected[:storage.start()].strip()
            if not re.search(r"\\b" + storage.group(1) + r"\\s*" + storage.group(2) + r"\\b", title, re.I):
                return False
        model_matches = candidate_model == model_expected or (
            not model_expected.endswith(" 5g") and candidate_model == model_expected + " 5g"
        )
        return model_matches
    # Non-mobile listings require a manufacturer model code, never RAM matching.
    code = str(row.get("model_code") or "").strip()
    return bool(
        _tokens(item.get("brand")) == _tokens(row["brand"])
        and code
        and re.search(r"(?<![a-z0-9])" + re.escape(code) + r"(?![a-z0-9])", title, re.I)
    )


def image_references(item):
    values = item.get("images") or []
    if isinstance(values, str):
        values = [values]
    if item.get("image_url"):
        values = [*values, item["image_url"]] if isinstance(values, list) else [item["image_url"]]
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if not isinstance(value, str):
            continue
        url = urlsplit(value)
        if (url.scheme == "https" and url.hostname in {"rukminim1.flixcart.com", "rukminim2.flixcart.com", "rukminim3.flixcart.com"}
                and not url.username and not url.password and url.port in {None, 443}):
            result.append(value)
    return list(dict.fromkeys(result))[:8]


def audit_response(payload, row, observed_at, pincode):
    data = payload.get("data") if isinstance(payload, dict) else None
    if (payload.get("status") != "success" or not isinstance(data, dict)
            or data.get("platform") != "Flipkart" or not isinstance(data.get("products"), list)):
        raise ValueError("Unexpected provider response")
    candidates = []
    for item in data["products"]:
        if not listing_candidate(item, row):
            continue
        available = item.get("available")
        price = None if isinstance(item.get("offer_price"), bool) else _positive_price(item.get("offer_price"))
        if type(available) is not bool or item.get("currency") != "INR" or (available and price is None):
            continue
        candidates.append({
            "retailer_product_id": item["id"], "title": item["name"],
            "quantity": str(item.get("quantity") or ""), "product_url": item["deeplink"],
            "price_observation": price if available else None,
            "availability_observation": "in_stock" if available else "out_of_stock",
            "currency": "INR", "image_references": image_references(item),
            "image_publish_eligible": False, "image_rights_status": "PERMISSION_NOT_ESTABLISHED",
            "exact_canonical_variant_verified": False, "publishable": False,
        })
    photo = row.get("photo") or {}
    return {
        "audit_id": row["audit_id"], "category": row["category"], "query": query_for(row),
        "source": SOURCE, "observed_at_utc": observed_at, "pincode": pincode,
        "status": "MODEL_CANDIDATES_REQUIRE_VARIANT_REVIEW" if candidates else "NO_STRICT_MODEL_CANDIDATE",
        "existing_photo_reference": photo or None,
        "existing_image_publish_eligible": row.get("image_publish_eligible", False),
        "candidates": candidates, "publishable": False,
    }


def run(targets, connector, *, max_calls=0, delay_seconds=1.0, checkpoint=None):
    if not 0 <= max_calls <= 272 or delay_seconds < 1:
        raise ValueError("max_calls must be 0..272; delay must be at least one second")
    report = {"schema_version": 1, "mode": "PRIVATE_RESEARCH_OBSERVATIONS", "source": SOURCE,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "calls_attempted": 0,
              "publishable": False, "records": [], "stopped_reason": None}
    report["existing_photo_coverage"] = {
        "mobile_photo_references": sum(bool(row.get("photo")) for row in targets if row["category"] == "mobiles"),
        "mobile_missing_photo": sum(not bool(row.get("photo")) for row in targets if row["category"] == "mobiles"),
        "note": "Existing catalogue evidence only; no new image rights or visual verification asserted",
    }
    for row in targets:
        if report["calls_attempted"] >= max_calls:
            report["records"].append({"audit_id": row["audit_id"], "category": row["category"],
                                      "status": "NOT_REQUESTED_CALL_LIMIT", "publishable": False})
            continue
        report["calls_attempted"] += 1
        try:
            payload, observed = connector.search(query_for(row))
            record = audit_response(payload, row, observed, connector.pincode)
        except Exception as error:
            # Stop on ANY error, not just auth/quota: prevents hundreds of bad calls.
            report["stopped_reason"] = "PROVIDER_OR_VALIDATION_ERROR"
            record = {"audit_id": row["audit_id"], "category": row["category"],
                      "status": "REQUEST_FAILED", "error_class": type(error).__name__, "publishable": False}
        report["records"].append(record)
        if checkpoint:
            checkpoint(report)
        if report["stopped_reason"]:
            break
        if report["calls_attempted"] < min(len(targets), max_calls):
            time.sleep(delay_seconds)
    completed_ids = {r["audit_id"] for r in report["records"]}
    for row in targets:
        if row["audit_id"] not in completed_ids:
            report["records"].append({"audit_id": row["audit_id"], "category": row["category"],
                                      "status": "NOT_REQUESTED_AFTER_ERROR", "publishable": False})
    report["status_counts"] = dict(Counter(r["status"] for r in report["records"]))
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    if checkpoint:
        checkpoint(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--category", choices=["all", "mobiles", "tvs", "earbuds"], default="all")
    parser.add_argument("--max-calls", type=int, default=0)
    parser.add_argument("--pincode", default="110001")
    parser.add_argument("--output", type=Path, default=ROOT / "private_observations/quickcommerce_audit.json")
    args = parser.parse_args()
    if not args.live and args.max_calls:
        parser.error("--max-calls requires --live")
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "private_observations").resolve()):
        parser.error("Output must stay under private_observations, outside public build inputs")
    output.parent.mkdir(parents=True, exist_ok=True)
    def save(report):
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report = run(load_targets(args.category), QuickCommerceFlipkartConnector(pincode=args.pincode),
                 max_calls=args.max_calls if args.live else 0, checkpoint=save)
    print(json.dumps({key: report[key] for key in ("calls_attempted", "status_counts", "stopped_reason", "publishable")}))
    return 1 if report["stopped_reason"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

