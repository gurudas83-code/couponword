import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))
from candidate_funnel_audit import (  # noqa: E402
    audit_candidate,
    coverage_row,
    stable_trace_id,
    summarize_traces,
)


def candidate(**overrides):
    row = {
        "canonical_product_id": "cw-mobile-1",
        "retailer_product_id": "B000000001",
        "source_url": "https://example.test/p/1",
        "brand": "Test",
        "model": "Test Phone",
        "variant": "8GB/128GB",
        "research": True,
        "canonical": True,
        "exact_variant": True,
        "product_dna": True,
        "retailer_mapping": True,
        "fresh_offer": True,
        "verified_price": 19999,
        "ranking_eligible": True,
        "displayed": True,
    }
    row.update(overrides)
    return row


class Issue10CandidateFunnelTests(unittest.TestCase):
    def test_trace_id_is_stable_and_position_independent(self):
        first = stable_trace_id(candidate())
        second = stable_trace_id(candidate(unrelated_position=99))
        self.assertEqual(first, second)

    def test_first_blocker_is_unique_and_secondary_reasons_are_retained(self):
        result = audit_candidate(candidate(canonical=False, fresh_offer=False), budget=20000)
        self.assertEqual(result["first_blocker"], "canonical")
        self.assertEqual(result["secondary_blockers"][0]["stage"], "fresh_offer")

    def test_budget_is_strict_and_unknown_price_is_not_pass(self):
        over = audit_candidate(candidate(verified_price=20001), budget=20000)
        unknown = audit_candidate(candidate(verified_price=None), budget=20000)
        self.assertEqual(over["first_blocker"], "strict_budget")
        self.assertEqual(unknown["first_blocker"], "fresh_offer")

    def test_no_double_counting_in_summary(self):
        rows = [
            audit_candidate(candidate(canonical=False)),
            audit_candidate(candidate(fresh_offer=False)),
            audit_candidate(candidate()),
        ]
        summary = summarize_traces(rows)
        self.assertEqual(summary["candidate_count"], 3)
        self.assertEqual(summary["first_blocker_breakdown"]["canonical"], 1)
        self.assertEqual(summary["first_blocker_breakdown"]["PASS"], 1)

    def test_coverage_row_keeps_specialist_top3_empty_when_no_specialist_evidence(self):
        row = coverage_row([candidate(), candidate(canonical_product_id="cw-mobile-2")], 20000)
        self.assertEqual(row["overall_top3_count"], 2)
        self.assertEqual(row["camera_top3_count"], 0)
        self.assertEqual(row["gaming_top3_count"], 0)

    def test_fifty_frozen_replays_are_deterministic(self):
        outputs = [coverage_row([candidate(), candidate(verified_price=35000)], 30000) for _ in range(50)]
        self.assertTrue(all(item == outputs[0] for item in outputs))


if __name__ == "__main__":
    unittest.main()
