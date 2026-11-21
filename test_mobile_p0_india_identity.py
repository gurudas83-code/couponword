"""Fail-closed tests for P0 India model/variant evidence and Top 30 annotations."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from python.mobile_p0_identity import ROOT, enrich_public_catalogue, top30_report


class IndiaIdentityP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = json.loads((ROOT / "public/data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig"))
        cls.catalogue = enrich_public_catalogue(copy.deepcopy(raw), ROOT)
        cls.by_key = {c["model_key"]: c for c in cls.catalogue["model_cards"]}

    def test_all_232_have_explicit_identity_and_nonbuyable_status(self):
        cards = self.catalogue["model_cards"]
        self.assertEqual(len(cards), 232)
        self.assertEqual(len(self.by_key), 232)
        for card in cards:
            identity = card["india_identity_evidence"]
            self.assertIn(identity["status"], {"INDIA_EXACT_VARIANT_DOCUMENTED", "INDIA_IDENTITY_OR_VARIANT_UNCONFIRMED"})
            self.assertFalse(identity["current_stock_verified"])
            self.assertFalse(identity["current_price_verified"])
            self.assertFalse(identity["purchase_eligible"])
            self.assertEqual(identity["status"] == "INDIA_EXACT_VARIANT_DOCUMENTED",
                             len(identity["verified_variants"]) > 0)
            for variant in identity["verified_variants"]:
                self.assertGreater(variant["ram_gb"], 0)
                self.assertGreater(variant["storage_gb"], 0)
                self.assertTrue(variant["source_url"].startswith("https://"))

    def test_new_official_india_exact_variants_and_existing_frozen_variants(self):
        expected = {
            "nothing|phone 3a": {(8, 128)},
            "oppo|k13 5g": {(8, 128), (8, 256)},
            "oneplus|nord 6": {(8, 256), (12, 256)},
            "vivo|t5x 5g": {(6, 128), (8, 256)},
            "samsung|galaxy a36 5g": {(8, 128), (8, 256), (12, 256)},
            "samsung|galaxy a56 5g": {(8, 128), (8, 256), (12, 256)},
        }
        for key, variants in expected.items():
            found = {(row["ram_gb"], row["storage_gb"])
                     for row in self.by_key[key]["india_identity_evidence"]["verified_variants"]}
            self.assertTrue(variants <= found, (key, variants - found))
        self.assertEqual(self.by_key["poco|m8 power 5g"]["india_identity_evidence"]["status"],
                         "INDIA_IDENTITY_OR_VARIANT_UNCONFIRMED")

    def test_top30_matches_exact_indian_variant_not_an_uncertain_model_name(self):
        report = top30_report(self.catalogue, ROOT)
        models = report["models"]
        self.assertEqual(len(models), 30)
        self.assertEqual({m["priority_index"] for m in models}, set(range(1, 31)))
        self.assertTrue(any(m["india_source_verified_variants"] for m in models))
        self.assertTrue(any(not m["india_source_verified_variants"] for m in models))
        self.assertEqual(report["counts"]["live_authorized_buying_candidates"], 0)
        for model in models:
            pairs = {(v["ram_gb"], v["storage_gb"]) for v in model["india_source_verified_variants"]}
            for offer in model["historical_retailer_evidence_matching_india_variant"]:
                self.assertIn((offer["ram_gb"], offer["storage_gb"]), pairs)
                self.assertFalse(offer["purchase_eligible"])
                self.assertEqual(offer["observation_scope"], "HISTORICAL_THIRD_PARTY_NOT_AUTHORIZED_OFFER")
            self.assertFalse(model["buying_recommendation_eligible"])
            self.assertFalse(model["current_authorized_offer_verified"])

    def test_rejects_malicious_cross_model_and_duplicate_manufacturer_evidence(self):
        from python import mobile_p0_identity as source
        original_read = source._read
        bad = copy.deepcopy(original_read(ROOT, "data/mobile_p0_india_variant_evidence_20261121.json"))
        bad["records"][0]["model_key"] = "poco|m8 power 5g"
        with patch.object(source, "_read", side_effect=lambda root, path:
                          bad if path.endswith("mobile_p0_india_variant_evidence_20261121.json")
                          else original_read(root, path)):
            with self.assertRaises(ValueError):
                enrich_public_catalogue(copy.deepcopy(self.catalogue), ROOT)


if __name__ == "__main__":
    unittest.main()
