"""Merge reviewed offer evidence without resetting observation timestamps."""
import json
from datetime import datetime
from pathlib import Path
from retailer_contract import RetailerOffer
from price_evidence import PriceEvidence
from evidence_validator import validate_price_evidence
from retailer_product_registry import find_canonical_product_id

REVIEWED_FILE = Path(__file__).resolve().parent.parent / "data" / "phase_e_f70e_comparison_evidence.json"


def merge_reviewed_offers(database, product_id, path=REVIEWED_FILE):
    result = dict(database)
    records = list(database.get("offers") or [])
    result["offers"] = records
    try:
        proof = json.loads(path.read_text(encoding="utf-8-sig"))
        canonical = proof["canonical_product"]
        if canonical["product_id"] != product_id:
            return result
        for record in proof["offers"]:
            offer = RetailerOffer(**record)
            if offer.product_id != product_id:
                continue
            if any(str(getattr(offer, key)).casefold() != str(canonical[key]).casefold()
                   for key in ("brand", "model", "variant")):
                continue
            if find_canonical_product_id(retailer=offer.retailer,
                                         retailer_product_id=offer.retailer_product_id) != product_id:
                continue
            evidence = next((PriceEvidence(**e) for e in proof["evidence"]
                             if e["retailer"] == offer.retailer and
                             e["retailer_product_id"] == offer.retailer_product_id), None)
            if evidence is None or not validate_price_evidence(offer, evidence)[0]:
                continue
            if offer.price != evidence.price or offer.last_checked != evidence.observed_at:
                continue
            observed = datetime.fromisoformat(offer.last_checked)
            if observed.tzinfo is None:
                continue
            key = (product_id, offer.retailer, offer.retailer_product_id)
            index = next((i for i, row in enumerate(records)
                          if (row.get("product_id"), row.get("retailer"),
                              row.get("retailer_product_id")) == key), None)
            if index is None:
                records.append(record)
            else:
                try:
                    if observed > datetime.fromisoformat(records[index]["last_checked"]):
                        records[index] = record
                except (ValueError, TypeError, KeyError):
                    continue
    except (OSError, ValueError, TypeError, KeyError):
        return result
    # Existing comparison freshness checks still apply to all returned offers.
    return result
