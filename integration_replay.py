"""Fifty identical deterministic replays of the integrated synthetic flow."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

import integration_smoke as flow
from api_contract import apply_response_contract
from shared_candidate_pool import build_shared_candidate_pool, rank_shared_pool_categories


def replay_summary() -> dict:
    candidates = [
        flow.make_candidate("fixture-a", 15000, 95, 70, 60),
        flow.make_candidate("fixture-b", 16000, 80, 95, 75),
        flow.make_candidate("fixture-c", 17000, 70, 80, 98),
    ]
    pool = build_shared_candidate_pool(
        query_id="frozen-integrated-under-18000",
        budget_max=18000,
        candidates=candidates,
        evidence_version="integration-evidence-v1",
        now=flow.NOW,
    )
    categories = rank_shared_pool_categories(pool)
    selected = copy.deepcopy(candidates[0]["offers"][0])
    rec = {
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
    output = apply_response_contract(
        {"schema_version": "1.1", "query": "Best phone under 18000", "intent": {"category": "smartphone", "budget_max": 18000, "priority_weights": {"budget": 20}}, "result_status": "PASS", "recommendations": [rec], "category_results": categories},
        "Best phone under 18000",
        now=flow.NOW,
    )
    return {
        "eligible_ids": tuple(pool["eligible_canonical_variant_ids"]),
        "category_orders": tuple((name, tuple(item["canonical_product_id"] for item in result["results"])) for name, result in sorted(categories.items())),
        "api_contract_version": output["api_contract_version"],
        "purchase_cta_eligible": output["recommendations"][0]["purchase_cta_eligible"],
    }


first = replay_summary()
for _ in range(49):
    assert replay_summary() == first
print({"replays": 50, "deterministic": True, "summary": first})
