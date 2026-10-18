import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATUS_PATH = ROOT / "data" / "phase_d_mobile_inventory_status.json"


def load_status():
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


class PhaseDMobileInventoryStatusTests(unittest.TestCase):
    def test_inventory_status_covers_existing_seed_without_promoting_unverified_models(self):
        payload = load_status()
        products = payload["products"]

        self.assertEqual(len(products), 187)
        self.assertEqual(payload["global_catalogue_summary"]["research_seed_entries"], 187)
        self.assertEqual(payload["global_catalogue_summary"]["fresh_in_stock_offers_current"], 0)
        self.assertEqual(payload["seed_intersection_summary"]["fresh_in_stock_offers_in_intersection"], 0)

        allowed_states = {
            "RESEARCH_ONLY",
            "OFFICIAL_EVIDENCE_VERIFIED",
            "PRIVATE_DNA_ADMITTED",
            "CANONICAL_SHOPPING_READY",
            "FRESH_OFFER_AVAILABLE",
        }
        self.assertLessEqual({item["coverage_state"] for item in products}, allowed_states)
        self.assertTrue(all(item.get("fresh_offer_available") is False for item in products))
        self.assertTrue(all(
            not item.get("canonical_product_id")
            for item in products
            if item["coverage_state"] in {"RESEARCH_ONLY", "OFFICIAL_EVIDENCE_VERIFIED", "PRIVATE_DNA_ADMITTED"}
        ))


    def test_inventory_status_does_not_claim_to_be_a_verified_launch_census(self):
        payload = load_status()

        self.assertIn("not a verified launch census", payload["scope"].lower())
        self.assertIn("does not make products recommendation-eligible", payload["scope"].lower())
