import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from resolver_engine import compare_identity


class ResolverModelFamilyTests(unittest.TestCase):
    def test_shared_number_does_not_cross_iphone_and_ipad_families(self):
        decision = compare_identity(
            expected_text="Apple iPhone 11 4GB RAM 64GB",
            candidate_title="iPad 11 specs",
            candidate_url="https://www.apple.com/ipad-11/specs/",
            expected_brand="Apple",
        )
        self.assertNotEqual(decision.decision, "verified")
        self.assertIn("No alphabetic model-family token matched", decision.reasons)

    def test_shared_se_generation_does_not_cross_iphone_and_watch_families(self):
        decision = compare_identity(
            expected_text="Apple iPhone SE 3 4GB RAM 64GB",
            candidate_title="Apple Watch SE 3 specs",
            candidate_url="https://www.apple.com/apple-watch-se-3/specs/",
            expected_brand="Apple",
        )
        self.assertNotEqual(decision.decision, "verified")
        self.assertIn("Expected Apple family token missing: iphone", decision.reasons)

    def test_exact_model_family_still_matches(self):
        decision = compare_identity(
            expected_text="Samsung Galaxy A56 5G",
            candidate_title="Samsung Galaxy A56 5G specifications",
            candidate_url="https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a56-5g/",
            expected_brand="Samsung",
        )
        self.assertEqual(decision.decision, "verified")


if __name__ == "__main__":
    unittest.main()
