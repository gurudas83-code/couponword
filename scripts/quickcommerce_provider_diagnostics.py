"""Small private schema/identity diagnostic; no public writes, images or retries."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

QUERIES = ["Samsung Galaxy A56 5G", "Google Pixel 9a", "iQOO 15",
           "Motorola Edge 60 Pro", "Nothing Phone (3a)",
           "Xiaomi L55MC-IN TV", "OnePlus Nord Buds 3r E517A"]
FIELDS = {"id", "item_id", "name", "brand", "available", "offer_price", "price",
          "mrp", "quantity", "currency", "deeplink", "model", "model_code",
          "attributes", "specifications"}

def main():
    connector = QuickCommerceFlipkartConnector()
    rows = []
    calls = [("search", platform, {"q": query}) for query in QUERIES for platform in ("Amazon", "Flipkart")]
    calls += [("item", "Flipkart", {"item_id": "MOBHQBDXXJUDBFVH"}),
              ("item", "Amazon", {"item_id": "B0FDBB2VRC"}),
              ("item", "Croma", {"item_id": "317418"})]
    output = ROOT / "private_observations/provider_diagnostics.json"
    output.parent.mkdir(exist_ok=True)
    for endpoint, platform, params in calls:
        try:
            payload, observed = connector.fetch_observation(endpoint, platform, **params)
            data = payload.get("data") or {}
            items = data.get("products") if endpoint == "search" else data.get("items")
            rows.append({"endpoint": endpoint, "platform": platform, "params": params,
                         "observed_at": observed, "status": payload.get("status"),
                         "data_keys": list(data), "total_results": data.get("total_results"),
                         "items": [{k: v for k, v in item.items() if k in FIELDS}
                                   for item in (items or [])[:20]]})
        except Exception as error:
            rows.append({"endpoint": endpoint, "platform": platform, "params": params,
                         "error_class": type(error).__name__})
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1
        output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"completed": len(rows), "total": len(calls), "platform": platform}), flush=True)
        time.sleep(1)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
