from __future__ import annotations

import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from product_evidence_store import variant_signature_from_text
from shared_candidate_pool import (
    build_shared_candidate_pool,
    invalidate_if_stale,
    rank_shared_pool_categories,
    validate_category_results,
)
from weighted_fit_engine import calculate_product_fit


NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def offer(pid: str, price: int, *, retailer: str = "Amazon", suffix: str = "a", observed: datetime = NOW, variant: str = "8GB RAM 128GB storage", stock: str = "in_stock", authorized: bool = True) -> dict:
    return {
        "offer_id": f"{pid}-{suffix}",
        "product_id": pid,
        "retailer": retailer,
        "retailer_product_id": f"{retailer.lower()}-{pid}-{suffix}",
        "variant": variant,
        "title": f"{pid} {variant}",
        "price": price,
        "currency": "INR",
        "availability": stock,
        "source_authorized": authorized,
        "observed_at": observed.isoformat(),
    }


def product(pid: str, price: int, *, camera: float | None = 80, battery: float | None = 80, gaming: float | None = 80, offers: list[dict] | None = None, variant: str = "8GB RAM 128GB storage") -> dict:
    signals = {"budget": {"match": 1.0, "status": "verified"}, "camera": {"match": 0.8, "status": "verified"}}
    overall_intent = {"priority_weights": {"budget": 50, "camera": 50}, "hard_constraints": ["budget_max"]}
    draft = {"product_id": pid, "brand": "TestBrand", "model": pid, "price": price, "fit_signals": signals}
    assessment = calculate_product_fit(draft, overall_intent | {"budget_max": 20000})
    evidence = {}
    for name, value in (("camera", camera), ("battery", battery), ("gaming", gaming)):
        evidence[name] = {"sufficient": value is not None, "score": value, "reason": "fixture evidence" if value is not None else f"No comparable {name} evidence"}
    return {
        "canonical_product_id": pid,
        "brand": "TestBrand",
        "model": pid,
        "title": f"TestBrand {pid} {variant}",
        "variant": variant_signature_from_text(variant),
        "offers": offers if offers is not None else [offer(pid, price)],
        "overall_fit_assessment": assessment,
        "camera_evidence": evidence["camera"],
        "battery_evidence": evidence["battery"],
        "gaming_evidence": evidence["gaming"],
    }


class Issue15SharedPoolTests(unittest.TestCase):
    def build(self, candidates, budget=20000, constraints=None):
        return build_shared_candidate_pool(
            query_id="fixture-under-20000",
            budget_max=budget,
            candidates=candidates,
            constraints=constraints,
            evidence_version="fixture-evidence-v1",
            now=NOW,
        )

    def test_a_shared_pool_allows_distinct_category_orders(self):
        candidates = [
            product("atlas-a", 15000, camera=95, battery=70, gaming=60),
            product("atlas-b", 16000, camera=80, battery=95, gaming=75),
            product("atlas-c", 17000, camera=70, battery=80, gaming=98),
            product("atlas-d", 18000, camera=75, battery=75, gaming=85),
            product("atlas-e", 19000, camera=65, battery=65, gaming=70),
        ]
        pool = self.build(candidates)
        results = rank_shared_pool_categories(pool)
        self.assertEqual(len(pool["candidates"]), 5)
        self.assertEqual(results["camera"]["results"][0]["canonical_product_id"], "atlas-a")
        self.assertEqual(results["battery"]["results"][0]["canonical_product_id"], "atlas-b")
        self.assertEqual(results["gaming"]["results"][0]["canonical_product_id"], "atlas-c")
        self.assertEqual(validate_category_results(pool, results), [])

    def test_b_partial_camera_is_honest(self):
        pool = self.build([product("a", 15000, camera=90), product("b", 16000, camera=80), product("c", 17000, camera=None)])
        results = rank_shared_pool_categories(pool)
        self.assertEqual(results["overall"]["result_count"], 3)
        self.assertEqual(results["camera"]["result_count"], 2)
        self.assertEqual(results["camera"]["category_evidence_shortages"][0]["status"], "CATEGORY_EVIDENCE_INSUFFICIENT")

    def test_c_partial_battery_does_not_use_capacity_as_endurance(self):
        pool = self.build([product("a", 15000, battery=95), product("b", 16000, battery=None), product("c", 17000, battery=None)])
        results = rank_shared_pool_categories(pool)
        self.assertEqual(results["battery"]["result_count"], 1)

    def test_d_partial_gaming_is_honest(self):
        pool = self.build([product("a", 15000, gaming=95), product("b", 16000, gaming=85), product("c", 17000, gaming=None)])
        self.assertEqual(rank_shared_pool_categories(pool)["gaming"]["result_count"], 2)

    def test_e_expired_offer_is_absent_from_all_categories(self):
        old = NOW - timedelta(hours=6, seconds=1)
        pool = self.build([product("expired", 15000, offers=[offer("expired", 15000, observed=old)])])
        self.assertEqual(pool["eligible_canonical_variant_ids"], [])
        self.assertIn("NO_CURRENT_VERIFIED_OFFER", pool["rejected_candidates"][0]["hard_eligibility_blockers"])

    def test_f_wrong_physical_variant_is_absent(self):
        wrong = product("wrong", 15000, offers=[offer("wrong", 15000, variant="6GB RAM 128GB storage")])
        pool = self.build([wrong])
        self.assertEqual(pool["eligible_canonical_variant_ids"], [])

    def test_g_multiple_retailer_offers_create_one_product_slot(self):
        offers = [offer("multi", 16000, suffix="amazon"), offer("multi", 15500, retailer="Flipkart", suffix="flip")]
        pool = self.build([product("multi", 16000, offers=offers)])
        results = rank_shared_pool_categories(pool)
        self.assertEqual(results["overall"]["result_count"], 1)
        self.assertEqual(pool["eligible_offer_ids"], ["multi-flip", "multi-amazon"])

    def test_h_strict_18000_ceiling_excludes_19000(self):
        pool = self.build([product("over", 19000)], budget=18000)
        self.assertFalse(pool["eligible_canonical_variant_ids"])

    def test_i_stretch_candidate_is_not_in_strict_pool(self):
        strict = self.build([product("strict", 18000), product("stretch", 19000)], budget=18000)
        self.assertEqual(strict["eligible_canonical_variant_ids"], ["strict"])

    def test_j_zero_valid_offers_returns_zero_everywhere(self):
        candidates = [product("no-offer", 15000, offers=[])]
        pool = self.build(candidates)
        results = rank_shared_pool_categories(pool)
        self.assertTrue(all(section["result_count"] == 0 for section in results.values()))

    def test_k_offer_expiry_invalidates_cached_shared_pool(self):
        pool = self.build([product("soon", 15000, offers=[offer("soon", 15000, observed=NOW - timedelta(hours=5, minutes=59))])])
        invalid = invalidate_if_stale(pool, now=NOW + timedelta(minutes=2))
        self.assertFalse(invalid["cache_valid"])
        self.assertEqual(invalid["hard_eligibility_status"], "POOL_INVALIDATED_OFFER_EXPIRED")

    def test_l_category_version_mismatch_is_rejected(self):
        pool = self.build([product("one", 15000)])
        results = rank_shared_pool_categories(pool)
        results["camera"]["candidate_pool_version"] = "old-version"
        self.assertIn("camera: candidate-pool version mismatch", validate_category_results(pool, results))

    def test_brand_and_variant_constraints_are_common_gates(self):
        candidate = product("one", 15000, variant="8GB RAM 128GB storage")
        pool = self.build([candidate], constraints={"brands": ["OtherBrand"], "ram_gb": "8", "storage_gb": "128"})
        self.assertFalse(pool["eligible_canonical_variant_ids"])

    def test_fifty_identical_replays_are_deterministic(self):
        candidates = [product("a", 15000, camera=90, battery=75, gaming=60), product("b", 16000, camera=80, battery=95, gaming=85)]
        first = self.build(candidates)
        first_results = rank_shared_pool_categories(first)
        for _ in range(49):
            replay = self.build(copy.deepcopy(candidates))
            self.assertEqual(replay["candidate_pool_version"], first["candidate_pool_version"])
            self.assertEqual(rank_shared_pool_categories(replay), first_results)


if __name__ == "__main__":
    unittest.main()
