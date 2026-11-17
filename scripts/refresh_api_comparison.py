"""Explicitly bounded API searches for existing catalogue identities; no retries."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-calls", type=int, default=0)
    args = parser.parse_args()
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
