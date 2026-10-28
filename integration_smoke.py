"""Read-only integrated synthetic flow for the unified candidate."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from api_contract import API_CONTRACT_VERSION, apply_response_contract
from cta_eligibility import attach_cta_eligibility
from evidence_freshness import is_offer_fresh
from offer_normalizer import normalize_offer
from product_evidence_store import variant_signature_from_text
from shared_candidate_pool import build_shared_candidate_pool, rank_shared_pool_categories
from stretch_budget_adapter import evaluate_optional_stretch
from weighted_fit_engine import calculate_product_fit


NOW = datetime.now(timezone.utc)
VARIANT_TEXT = "8GB RAM 128GB storage"


def make_candidate(product_id: str, price: int, camera: float, battery: float, gaming: float) -> dict:
    raw_offer = {
        "product_id": product_id,
        "retailer_product_id": f"B0-{product_id}",
        "brand": "FixtureBrand",
        "model": product_id,
        "variant": VARIANT_TEXT,
        "title": f"FixtureBrand {product_id} {VARIANT_TEXT}",
        "price": price,
        "currency": "INR",
        "availability": "in_stock",
        "product_url": f"https://www.amazon.in/dp/B0-{product_id}",
        "source": "amazon_primary_buybox",
        "confidence": 1.0,
        "last_checked": (NOW - timedelta(minutes=30)).isoformat(),
    }
    normalized_offer = normalize_offer("Amazon", raw_offer)
    assert is_offer_fresh(normalized_offer)
    offer = asdict(normalized_offer)
    offer["source_authorized"] = True
    offer["observed_at"] = offer["last_checked"]
    offer = attach_cta_eligibility(
        offer,
        product_id=product_id,
        variant=VARIANT_TEXT,
        now=NOW,
    )
    assert offer and offer["cta_eligibility"]["eligible"]
    fit = calculate_product_fit(
        {"product_id": product_id, "brand": "FixtureBrand", "model": product_id, "price": price,
         "fit_signals": {"budget": {"match": 1.0, "status": "verified"}, "camera": {"match": camera / 100, "status": "verified"}}},
        {"budget_max": 20000, "hard_constraints": ["budget_max"], "priority_weights": {"budget": 50, "camera": 50}},
    )
    return {
        "canonical_product_id": product_id,
        "brand": "FixtureBrand",
        "model": product_id,
        "title": f"FixtureBrand {product_id} {VARIANT_TEXT}",
        "variant": variant_signature_from_text(VARIANT_TEXT),
        "offers": [offer],
        "overall_fit_assessment": fit,
        "camera_evidence": {"sufficient": True, "score": camera, "reason": "fixture evidence"},
        "battery_evidence": {"sufficient": True, "score": battery, "reason": "fixture evidence"},
        "gaming_evidence": {"sufficient": True, "score": gaming, "reason": "fixture evidence"},
    }


def main() -> None:
    candidates = [
        make_candidate("fixture-a", 15000, 95, 70, 60),
        make_candidate("fixture-b", 16000, 80, 95, 75),
        make_candidate("fixture-c", 17000, 70, 80, 98),
    ]
    pool = build_shared_candidate_pool(
        query_id="integrated-under-18000",
        budget_max=18000,
        candidates=candidates,
        evidence_version="integration-evidence-v1",
        now=NOW,
    )
    category_results = rank_shared_pool_categories(pool)
    assert len(pool["eligible_canonical_variant_ids"]) == 3
    assert category_results["camera"]["results"][0]["canonical_product_id"] == "fixture-a"
    assert category_results["battery"]["results"][0]["canonical_product_id"] == "fixture-b"
    assert category_results["gaming"]["results"][0]["canonical_product_id"] == "fixture-c"

    selected = candidates[0]["offers"][0]
    recommendation = {
        "rank": 1,
        "product_id": "fixture-a",
        "canonical_product_id": "fixture-a",
        "title": candidates[0]["title"],
        "brand": "FixtureBrand",
        "identity_evidence": {"status": "catalogued_exact_variant", "variant": {"ram_gb": "8", "storage_gb": "128"}},
        "retailer_offers": [selected],
        "best_offer": selected,
        "current_offer_verified": True,
        "purchase_cta_eligible": True,
        "provenance": {"price_evidence": {"verified": True, "price": 15000, "currency": "INR", "source_url": selected["product_url"], "retailer_product_id": selected["retailer_product_id"], "availability": "in_stock", "verified_at": selected["last_checked"]}},
    }
    payload = {"schema_version": "1.1", "query": "Best phone under 18000", "intent": {"category": "smartphone", "budget_max": 18000, "priority_weights": {"budget": 20}}, "result_status": "PASS", "recommendations": [recommendation], "category_results": category_results}
    output = apply_response_contract(payload, "Best phone under 18000", now=NOW)
    assert output["api_contract_version"] == API_CONTRACT_VERSION
    assert output["recommendations"][0]["current_offer_verified"] is True
    assert output["recommendations"][0]["purchase_cta_eligible"] is True

    stretch = evaluate_optional_stretch(
        user_budget_inr=18000,
        user_text="Best phone under 18000",
        intent={"category": "smartphone"},
        strict_pool=pool,
        stretch_candidates=candidates,
        enabled=False,
        evidence_version="integration-evidence-v1",
        scoring_version="approved-scoring-v1",
        now=NOW,
    )
    assert stretch["stretch_enabled"] is False

    baseline = json.loads((Path("data") / "retailer_offers.json").read_text(encoding="utf-8"))
    print(json.dumps({
        "pipeline": ["normalize_offer", "freshness", "cta_eligibility", "shared_pool", "category_ranking", "api_contract", "stretch_adapter"],
        "candidate_count": len(pool["eligible_canonical_variant_ids"]),
        "category_orders": {name: [item["canonical_product_id"] for item in result["results"]] for name, result in category_results.items()},
        "api_contract_version": output["api_contract_version"],
        "purchase_cta_eligible": output["recommendations"][0]["purchase_cta_eligible"],
        "stretch_enabled": stretch["stretch_enabled"],
        "real_repository_offer_records_observed": len(baseline.get("offers", [])),
        "real_repository_mutated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
