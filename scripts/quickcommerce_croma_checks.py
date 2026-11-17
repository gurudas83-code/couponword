"""Check only already-reviewed exact Croma product IDs, once each."""
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

def main():
    data = json.loads((ROOT / "data/india_tv_earbuds_40_catalogue.json").read_text(encoding="utf-8"))
    connector = QuickCommerceFlipkartConnector()
    rows = []
    output = ROOT / "private_observations/croma_checks.json"
    output.parent.mkdir(exist_ok=True)
    for card in data["records"]:
        source = card["retailers"]["croma"]
        match = re.search(r"/p/(\d{5,9})/?$", source["retailer_research_url"])
        if not source.get("exact_model_link_verified") or not match:
            continue
        try:
            payload, observed = connector.fetch_observation("item", "Croma", item_id=match.group(1))
            body = payload.get("data") or {}
            rows.append({"endpoint": "item", "model_key": card["id"], "platform": "Croma",
                         "params": {"item_id": match.group(1)}, "status": payload.get("status"),
                         "observed_at": observed, "items": [
                             {k: v for k, v in item.items() if k in {"id", "item_id", "name", "brand",
                              "available", "price", "mrp", "quantity", "currency", "deeplink", "model_code"}}
                             for item in body.get("items", [])]})
        except Exception as error:
            rows.append({"endpoint": "item", "model_key": card["id"], "platform": "Croma",
                         "error_class": type(error).__name__, "http_status": getattr(error, "code", None)})
            if getattr(error, "code", None) in {401, 403, 429}:
                break
        output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(1)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"checked": len(rows), "errors": sum("error_class" in row for row in rows)}))

if __name__ == "__main__":
    main()
