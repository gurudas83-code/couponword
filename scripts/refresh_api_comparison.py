"""Explicitly bounded API searches for existing catalogue identities; no retries."""
import argparse
import os
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector
from scripts.build_price_evidence_coverage import build, positive_historical_observations
from build_multi_retailer_public import build_observation_snapshot

FIELDS = {"id", "item_id", "name", "brand", "available", "offer_price", "price",
          "mrp", "quantity", "currency", "deeplink", "model", "model_code"}


def planned_queries():
    """Research only the fixed Top-30 mobile worklist; never other product types."""
    pilot = json.loads((ROOT / "data/top30_research_pilot_20261113.json").read_text(encoding="utf-8"))
    selected = pilot.get("selected_models") or []
    keys = [row["model_key"] for row in selected]
    if len(keys) != 30 or len(set(keys)) != 30:
        raise ValueError("Approved Top-30 worklist is invalid")
    mobile = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig"))["model_cards"]
    cards = {card["model_key"]: card for card in mobile}
    if any(key not in cards for key in keys):
        raise ValueError("Top-30 research model is missing from catalogue")
    calls = []
    for key in keys:
        card = cards[key]
        query = card["model"] if card["model"].lower().startswith(card["brand"].lower() + " ") else card["brand"] + " " + card["model"]
        calls.append((key, "Flipkart", query))
    return calls

def missing_price_cards(refresh_historical=False):
    report = build()
    queue = report["verification_queue"]
    if refresh_historical:
        queue = [row for row in report["model_rows"] if row.get("source_date", "") and
                 row["source_date"][:10] < "2026-11-19"]
    cards = json.loads(
        (ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig")
    )["model_cards"]
    missing = {row["model_key"] for row in queue}
    return [card for card in cards if card["model_key"] in missing]


def refresh_missing_prices(max_calls, refresh_historical=False):
    cards = missing_price_cards(refresh_historical)
    output = ROOT / "private_observations" / "missing_mobile_api_prices.json"
    output.parent.mkdir(exist_ok=True)
    records = []
    errors = []
    attempts = 0
    connector = QuickCommerceFlipkartConnector(pincode="110001")

    def save():
        snapshot = build_observation_snapshot({}, cards, records)
        priced = {
            key for key, variants in snapshot["models"].items()
            if positive_historical_observations(variants, key)
        }
        remaining = [card["model_key"] for card in cards if card["model_key"] not in priced]
        result = {
            "calls_attempted": attempts,
            "targeted_models": len(cards),
            "models_with_price": len(priced),
            "remaining_model_keys": remaining,
            "errors": errors,
            "snapshot": snapshot,
        }
        temporary = output.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        temporary.replace(output)
        return priced

    priced = save()
    for platform in ("Flipkart", "Amazon"):
        for card in cards:
            key = card["model_key"]
            if key in priced:
                continue
            if attempts >= max_calls:
                return 0
            brand, model = card["brand"], card["model"]
            query = model if model.lower().startswith(brand.lower() + " ") else f"{brand} {model}"
            attempts += 1
            try:
                payload, observed = connector.fetch_observation("search", platform, q=query)
                data = payload.get("data") or {}
                if (payload.get("status") != "success" or data.get("platform") != platform
                        or not isinstance(data.get("products"), list)):
                    raise ValueError("Unexpected provider schema")
                records.append({
                    "model_key": key, "endpoint": "search", "platform": platform,
                    "params": {"q": query}, "status": "success", "observed_at": observed,
                    "items": [{k: v for k, v in item.items() if k in FIELDS}
                              for item in data["products"] if isinstance(item, dict)],
                })
            except Exception as error:
                errors.append({"model_key": key, "platform": platform,
                               "error_class": type(error).__name__,
                               "http_status": getattr(error, "code", None)})
                save()
                return 1
            priced = save()
            time.sleep(1)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-calls", type=int, default=0)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--missing-prices", action="store_true")
    scope.add_argument("--refresh-historical-dated-prices", action="store_true")
    args = parser.parse_args()
    if args.missing_prices or args.refresh_historical_dated_prices:
        if not 0 <= args.max_calls <= 464:
            parser.error("Missing-price research allows at most two calls per core model")
        if args.max_calls and not os.environ.get("QUICKCOMMERCE_API_KEY"):
            parser.error("QUICKCOMMERCE_API_KEY is required")
        return refresh_missing_prices(args.max_calls, args.refresh_historical_dated_prices)
    if not 0 <= args.max_calls <= 2:
        parser.error("Only 0..2 manually authorized Top-30 searches allowed")
    calls = planned_queries()
    connector = QuickCommerceFlipkartConnector()
    result = {"calls_attempted": 0, "records": [], "errors": [], "complete": False}
    output = ROOT / "private_observations/provider_refresh.json"
    output.parent.mkdir(exist_ok=True)
    for key, platform, query in calls[:args.max_calls]:
        result["calls_attempted"] += 1
        try:
            payload, observed = connector.fetch_observation("search", platform, q=query)
            data = payload.get("data") or {}
            if payload.get("status") != "success" or data.get("platform") != platform or not isinstance(data.get("products"), list):
                raise ValueError("Unexpected provider schema")
            result["records"].append({"model_key": key, "endpoint": "search", "platform": platform,
                "params": {"q": query}, "status": "success", "observed_at": observed,
                "items": [{k: v for k, v in item.items() if k in FIELDS} for item in data["products"]]})
        except Exception as error:
            result["errors"].append({"model_key": key, "platform": platform,
                                    "error_class": type(error).__name__, "http_status": getattr(error, "code", None)})
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if result["calls_attempted"] % 10 == 0:
            print(json.dumps({"completed": result["calls_attempted"], "cap": args.max_calls}), flush=True)
        time.sleep(1)
    result["complete"] = len(calls) == result["calls_attempted"]
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
