import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import shopping_intelligence_pipeline as pipeline


def _verified_identity():
    return SimpleNamespace(
        to_dict=lambda: {
            "score": 90,
            "decision": "verified",
            "reasons": [
                "Brand matched",
                "All identity-bearing model tokens matched",
                "Network generation matched",
            ],
        }
    )


def _runtime_profile(**kwargs):
    resolved = kwargs["resolved"]
    price_evidence = resolved.get("commerce_evidence") or {
        "verified": False,
        "price": None,
        "reason": "No structured retailer price found",
    }

    return {
        "product_id": "market-01",
        "title": "Redmi 13 5G Hawaiian Blue (8GB RAM, 128GB Storage)",
        "brand": "Redmi",
        "price": (
            price_evidence.get("price")
            if price_evidence.get("verified") is True
            else None
        ),
        "asin": None,
        "image_url": None,
        "commerce_provider": "test",
        "official_product_url": None,
        "market_source_url": "https://example.test/redmi-13-5g",
        "attributes": {},
        "features": [
            "Redmi 13 5G 8GB RAM 128GB Storage",
        ],
        "provenance": {
            "price_evidence": price_evidence,
            "resolver_mode": resolved.get("resolver_mode"),
            "resolver_status": resolved.get("status"),
            "resolver_identity_score": resolved.get("identity_score"),
            "resolver_match_score": resolved.get("match_score"),
        },
    }


def test_live_fast_verified_identity_survives_missing_price():
    candidate = {
        "candidate_id": "market-01",
        "title": "Redmi 13 5G Hawaiian Blue (8GB RAM, 128GB Storage)",
        "source_title": "Redmi 13 5G Hawaiian Blue (8GB RAM, 128GB Storage)",
        "source_url": "https://example.test/redmi-13-5g",
        "snippet": "8GB RAM 128GB Storage 5G",
        "brand": "Redmi",
        "price": None,
    }

    intent = {
        "intent": "feature_search",
        "category": "smartphone",
        "brands": ["Redmi"],
        "must_have": ["5g", "8gb_ram", "128gb_storage"],
        "preferred": [],
        "avoid": [],
        "features": ["5G"],
        "hard_constraints": [],
        "keywords": ["redmi", "13", "5g", "8gb", "128gb"],
        "budget_min": None,
        "budget_max": None,
    }

    identity = {
        "product_id": "market-01",
        "brand": "Redmi",
        "model": "13 5G",
        "search_name": "Redmi 13 5G 8GB 128GB",
        "asin": None,
    }

    discovery = {
        "candidates": [candidate],
        "exact_model_scope": {
            "active": True,
            "model_tokens": ["13"],
            "numeric_brand_pairs": [
                {"brand": "redmi", "model": "13"},
            ],
        },
    }

    fit = {
        "eligible": True,
        "fit_percent": 90,
        "raw_fit_percent": 90,
        "evidence_coverage_percent": 80,
        "recommendation_confidence": "high",
        "hard_constraint_failures": [],
        "criteria": [],
    }

    missing_price = {
        "verified": False,
        "price": None,
        "reason": "No structured retailer price found",
    }

    with (
        patch.object(pipeline, "parse_query", return_value=intent),
        patch.object(pipeline, "discover_market", return_value=discovery),
        patch.object(
            pipeline,
            "candidate_to_identity_input",
            return_value=({"title": candidate["title"]}, candidate["title"]),
        ),
        patch.object(pipeline, "call_build_identity", return_value=identity),
        patch.object(pipeline, "repair_identity", return_value=identity),
        patch.object(pipeline, "compare_identity", return_value=_verified_identity()),
        patch.object(pipeline, "build_price_evidence", return_value=missing_price),
        patch.object(pipeline, "find_verified_evidence", return_value=None),
        patch.object(pipeline, "runtime_profile_from_extraction", side_effect=_runtime_profile),
        patch.object(pipeline, "enrich_priority_evidence", side_effect=lambda **kw: kw["profile"]),
        patch.object(pipeline, "retrieve_missing_priority_evidence", side_effect=lambda **kw: kw["profile"]),
        patch.object(pipeline, "normalize_feature_corpus", side_effect=lambda values: list(values)),
        patch.object(pipeline, "build_fit_signals", return_value={}),
        patch.object(pipeline, "calculate_product_fit", return_value=fit),
        patch.object(pipeline, "criterion_groups", return_value=([], [], [])),
        patch.object(
            pipeline,
            "enrich_with_multi_retailer",
            return_value={
                "retailer_offers": [],
                "best_offer": None,
                "retailer_comparison_status": "unavailable",
            },
        ),
    ):
        result = pipeline.run_pipeline(
            query="Redmi 13 5G 8GB 128GB",
            max_candidates=1,
            max_results=1,
            live_fast=True,
        )

    assert result["stage_counts"]["recommendations_returned"] == 1
    assert result["result_status"] == "PASS"

    recommendation = result["recommendations"][0]
    assert recommendation["title"] == candidate["title"]
    assert recommendation["price"] is None

    price_evidence = recommendation["provenance"]["price_evidence"]
    assert price_evidence["verified"] is False
    assert price_evidence["price"] is None

    assert not any(
        failure.get("stage") == "live_commerce_verification"
        for failure in result["failures"]
    )


if __name__ == "__main__":
    test_live_fast_verified_identity_survives_missing_price()
    print("PASS: live-fast verified identity survives missing price")
