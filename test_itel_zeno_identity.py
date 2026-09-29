"""Protected itel Zeno identity and variant regression."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python"))

from product_identity_v2 import build_identity
from resolver_engine import compare_identity


class ItelZenoIdentityTests(unittest.TestCase):
    def test_brand_is_itel_and_models_remain_distinct(self):
        for model in ("Lite", "Pro"):
            with self.subTest(model=model):
                identity = build_identity({
                    "product_id": "probe", "title": f"Zeno 100 {model}",
                }, 1)
                self.assertEqual(identity["brand"], "itel")
                self.assertEqual(identity["model"], f"Zeno 100 {model}")
                self.assertEqual(identity["search_name"], f"itel Zeno 100 {model}")

    def test_retailer_without_maker_name_still_requires_exact_model(self):
        retailer = "https://www.amazon.in/dp/B0H8NW369M"
        for model, sibling in (("Lite", "Pro"), ("Pro", "Lite")):
            with self.subTest(model=model):
                requested = f"itel Zeno 100 {model}"
                exact = compare_identity(requested, f"Zeno 100 {model}",
                                         retailer, "itel")
                wrong = compare_identity(requested, f"Zeno 100 {sibling}",
                                         retailer, "itel")
                self.assertEqual(exact.decision, "verified")
                self.assertEqual(wrong.decision, "reject")

    def test_unrelated_retailer_title_and_wrong_official_domain_fail(self):
        requested = "itel Zeno 100 Lite"
        unrelated = compare_identity(requested, "Zeno 200 Lite",
                                     "https://www.amazon.in/dp/B0H8NW369M", "itel")
        wrong_domain = compare_identity(requested, "Zeno 100 Lite",
                                        "https://example.com/zeno-100-lite", "itel")
        self.assertNotEqual(unrelated.decision, "verified")
        self.assertNotEqual(wrong_domain.decision, "verified")


if __name__ == "__main__":
    unittest.main()
