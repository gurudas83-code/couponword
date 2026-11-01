import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

from python.mobile_research_catalogue import build_public_catalogue


ROOT = Path(__file__).resolve().parent


class MobileOfficialSpecEvidenceLedgerTests(unittest.TestCase):
    def test_ledger_is_sanitized_and_accepted(self):
        payload = json.loads(
            (ROOT / "data/mobile_official_spec_evidence.json").read_text(
                encoding="utf-8"
            )
        )
        records = payload.get("records") or []
        self.assertEqual(len(records), 9)
        self.assertEqual(
            sum(len(record.get("specifications") or {}) for record in records),
            46,
        )
        for record in records:
            self.assertEqual(record.get("review_status"), "candidate_ready")
            self.assertEqual(record.get("evidence_status"), "VERIFIED_SOURCE")
            self.assertTrue(str(record.get("official_url") or "").startswith("https://"))
            for field in (record.get("specifications") or {}).values():
                self.assertEqual(field.get("applicability"), "MODEL_SHARED")
                self.assertEqual(field.get("evidence_status"), "VERIFIED_SOURCE")
                self.assertTrue(str(field.get("source_url") or "").startswith("https://"))
                self.assertNotIn("price", str(field.get("value") or "").casefold())
                self.assertNotIn("cashback", str(field.get("value") or "").casefold())

    def test_catalogue_keeps_research_and_commerce_boundaries(self):
        catalogue = build_public_catalogue(ROOT)
        self.assertEqual(len(catalogue["model_cards"]), 232)
        self.assertEqual(len(catalogue["records"]), 235)
        self.assertEqual(
            sum(bool(card.get("specifications")) for card in catalogue["model_cards"]),
            40,
        )
        self.assertEqual(
            sum(len(card.get("specifications") or {}) for card in catalogue["model_cards"]),
            260,
        )
        for row in catalogue["records"]:
            commerce = row.get("commerce") or {}
            self.assertIsNone(commerce.get("price"))
            self.assertIsNone(commerce.get("stock"))
            self.assertFalse(commerce.get("purchase_cta_eligible"))


if __name__ == "__main__":
    unittest.main()
