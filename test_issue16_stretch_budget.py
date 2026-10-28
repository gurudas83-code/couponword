from __future__ import annotations

import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from stretch_budget_adapter import (  # noqa: E402
    DEFAULT_MAX_ADDITIONAL_INR,
    evaluate_optional_stretch,
    invalidate_stretch_result,
)
from weighted_fit_engine import MIN_EVIDENCE_COVERAGE_PERCENT, MIN_FIT_PERCENT  # noqa: E402


NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def offer(pid: str, price: int, *, observed: datetime = NOW, variant: str = "8GB RAM 128GB storage", stock: str = "in_stock", authorized: bool = True, retailer: str = "Amazon") -> dict:
    return {
        "offer_id": f"{pid}-{retailer.lower()}",
        "product_id": pid,
        "retailer": retailer,
        "retailer_product_id": f"{retailer.lower()}-{pid}",
        "variant": variant,
        "price": price,
        "currency": "INR",
        "availability": stock,
        "source_authorized": authorized,
        "observed_at": observed.isoformat(),
    }


def strict_pool(*candidates: dict, version: str = "issue15-pool-fixture-v1") -> dict:
    return {
        "candidate_pool_version": version,
        "strict_recommendations": [candidate["canonical_product_id"] for candidate in candidates],
        "candidates": list(candidates),
    }


def baseline(pid: str = "strict-a", price: int = 19500, score: float = 70) -> dict:
    return {
        "canonical_product_id": pid,
        "exact_variant_id": pid + "-8-128",
        "verified_price_inr": price,
        "comparison_score": score,
        "score_scale": "overall-absolute-v1",
        "score_version": "approved-score-v1",
    }


def stretch(pid: str = "stretch-a", price: int = 22000, score: float = 84, *, improvements=None, variant: str = "8GB RAM 128GB storage", observed: datetime = NOW, stock: str = "in_stock", authorized: bool = True, identity_conflict: bool = False) -> dict:
    return {
        "canonical_product_id": pid,
        "exact_variant_id": pid + "-8-128",
        "variant": {"ram_gb": "8", "storage_gb": "128"},
        "comparison_score": score,
        "score_scale": "overall-absolute-v1",
        "score_version": "approved-score-v1",
        "identity_conflict": identity_conflict,
        "verified_improvements": improvements if improvements is not None else [{
            "verified": True,
            "category": "overall",
            "evidence_kind": "comparable_measurement",
            "statement": "Verified higher overall capability on the approved common score.",
            "source_evidence": "frozen-comparable-overall-measurement-v1",
        }],
        "evidence_confidence": "high",
        "trade_offs": ["Requires additional spend."],
        "offers": [offer(pid, price, variant=variant, observed=observed, stock=stock, authorized=authorized)],
    }


def evaluate(candidate, *, budget=20000, text="best mobile under 20000", enabled=True, baseline_row=None, category="overall", allowance=5000):
    base = baseline_row or baseline()
    return evaluate_optional_stretch(
        user_budget_inr=budget,
        user_text=text,
        intent={"category": "smartphone", "budget_max": budget},
        strict_pool=strict_pool(base),
        stretch_candidates=[candidate],
        enabled=enabled,
        max_additional_inr=allowance,
        evidence_version="fixture-evidence-v1",
        scoring_version="approved-score-v1",
        category=category,
        now=NOW,
    )


class Issue16StretchBudgetTests(unittest.TestCase):
    def test_a_22000_candidate_is_separate_and_eligible_when_enabled(self):
        result = evaluate(stretch())
        suggestion = result["optional_stretch_recommendation"]
        self.assertEqual(result["stretch_status"], "OPTIONAL_STRETCH_VERIFIED")
        self.assertEqual(suggestion["stretch_canonical_product_id"], "stretch-a")
        self.assertEqual(suggestion["extra_above_budget_inr"], 2000)
        self.assertEqual(result["strict_recommendations"], ["strict-a"])

    def test_b_26000_candidate_is_outside_window(self):
        result = evaluate(stretch(price=26000))
        self.assertIsNone(result["optional_stretch_recommendation"])
        self.assertTrue(any("NO_VALID_STRETCH_OFFER" in str(item) for item in result["suppression_reasons"]))

    def test_c_arbitrary_10000_budget_uses_real_budget(self):
        result = evaluate(stretch(price=12000), budget=10000, text="best mobile under 10000")
        self.assertEqual(result["optional_stretch_recommendation"]["extra_above_budget_inr"], 2000)

    def test_d_explicit_hard_budget_suppresses_stretch(self):
        result = evaluate(stretch(), text="strictly under ₹20,000, cannot spend more")
        self.assertEqual(result["stretch_status"], "USER_OPTED_OUT")
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_e_higher_price_without_benefit_is_rejected(self):
        result = evaluate(stretch(improvements=[]))
        self.assertIsNone(result["optional_stretch_recommendation"])
        self.assertIn("NO_MEANINGFUL_VERIFIED_STRETCH", str(result["suppression_reasons"]))

    def test_f_megapixels_only_is_not_camera_quality(self):
        improvements = [{"verified": True, "category": "camera", "evidence_kind": "megapixels", "statement": "Higher MP", "source_evidence": "spec"}]
        result = evaluate(stretch(improvements=improvements), category="camera")
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_g_capacity_only_is_not_endurance(self):
        improvements = [{"verified": True, "category": "battery", "evidence_kind": "capacity_only", "statement": "Larger battery", "source_evidence": "spec"}]
        result = evaluate(stretch(improvements=improvements), category="battery")
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_h_ram_only_is_not_gaming_evidence(self):
        improvements = [{"verified": True, "category": "gaming", "evidence_kind": "ram_only", "statement": "More RAM", "source_evidence": "spec"}]
        result = evaluate(stretch(improvements=improvements), category="gaming")
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_i_wrong_variant_is_rejected(self):
        result = evaluate(stretch(variant="6GB RAM 128GB storage"))
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_j_expired_offer_is_rejected(self):
        result = evaluate(stretch(observed=NOW - timedelta(hours=6, seconds=1)))
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_k_unknown_stock_is_rejected(self):
        result = evaluate(stretch(stock="unknown"))
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_l_unverified_provider_is_rejected(self):
        result = evaluate(stretch(authorized=False))
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_m_duplicate_canonical_product_is_not_stretch(self):
        result = evaluate(stretch(pid="strict-a"))
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_n_incompatible_relative_score_scale_is_rejected(self):
        candidate = stretch()
        candidate["score_scale"] = "budget-relative-100"
        result = evaluate(candidate)
        self.assertIsNone(result["optional_stretch_recommendation"])
        self.assertIn("INCOMPARABLE_SCORE_REFERENCE", str(result["suppression_reasons"]))

    def test_o_zero_live_offers_is_honest(self):
        candidate = stretch()
        candidate["offers"] = []
        result = evaluate(candidate)
        self.assertEqual(result["stretch_status"], "NO_MEANINGFUL_VERIFIED_STRETCH")
        self.assertIsNone(result["optional_stretch_recommendation"])

    def test_p_expiry_invalidates_valid_cached_suggestion(self):
        result = evaluate(stretch())
        invalid = invalidate_stretch_result(result, now=NOW + timedelta(hours=6, seconds=1))
        self.assertEqual(invalid["stretch_status"], "STRETCH_OFFER_EXPIRED")
        self.assertIsNone(invalid["optional_stretch_recommendation"])

    def test_q_multiple_offers_selects_one_and_preserves_offer_id(self):
        candidate = stretch()
        candidate["offers"] = [offer("stretch-a", 22400, retailer="Flipkart"), offer("stretch-a", 22000, retailer="Amazon")]
        result = evaluate(candidate)
        self.assertEqual(result["optional_stretch_recommendation"]["offer_id"], "stretch-a-amazon")

    def test_r_18000_budget_is_not_rounded(self):
        result = evaluate(stretch(price=23000), budget=18000, text="best mobile under 18000")
        self.assertEqual(result["optional_stretch_recommendation"]["extra_above_budget_inr"], 5000)
        outside = evaluate(stretch(price=23001), budget=18000, text="best mobile under 18000")
        self.assertIsNone(outside["optional_stretch_recommendation"])

    def test_default_inactive_policy_and_scoring_constants(self):
        result = evaluate(stretch(), enabled=False)
        self.assertEqual(result["stretch_max_additional_inr"], DEFAULT_MAX_ADDITIONAL_INR)
        self.assertEqual(result["stretch_status"], "DISABLED_OWNER_REVIEW")
        self.assertEqual(MIN_FIT_PERCENT, 50)
        self.assertEqual(MIN_EVIDENCE_COVERAGE_PERCENT, 50)

    def test_fifty_identical_stretch_replays_are_deterministic(self):
        candidate = stretch()
        first = evaluate(candidate)
        for _ in range(49):
            replay = evaluate(copy.deepcopy(candidate))
            self.assertEqual(replay, first)


if __name__ == "__main__":
    unittest.main()
