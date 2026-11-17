"""Publish only attributed, explicitly parsed configurations; never offers/rankings."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from build_multi_retailer_public import build_observation_snapshot

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, action="append", default=[])
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8-sig"))
    diagnostics = []
    for path in args.diagnostics:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        diagnostics.extend(payload.get("records", []) if isinstance(payload, dict) else payload)
    cards = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig"))["model_cards"]
    categories = json.loads((ROOT / "data/india_tv_earbuds_40_catalogue.json").read_text(encoding="utf-8-sig"))["records"]
    cards += [dict(row, model_key=row["id"]) for row in categories]
    result = build_observation_snapshot(audit, cards, diagnostics)
    output = ROOT / "data/retailer_price_observations.json"
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(result["counts"]))

if __name__ == "__main__":
    main()
