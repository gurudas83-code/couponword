import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from intent_engine import canonical_intent_signature, canonical_intent_signature_hash, parse_query


class PhaseEQueryConsistencyTests(unittest.TestCase):
    def test_budget_spellings_share_semantic_signature(self):
        queries = (
            "mobile under 30000",
            "mobile under 30k",
            "mobile under 30 k",
            "mobile under 30,000",
        )
        signatures = {canonical_intent_signature(query) for query in queries}
        hashes = {canonical_intent_signature_hash(query) for query in queries}
        self.assertEqual(len(signatures), 1)
        self.assertEqual(len(hashes), 1)
        intent = parse_query(queries[0])
        self.assertEqual(intent["category"], "smartphone")
        self.assertEqual(intent["budget_max"], 30000)

    def test_meaningful_constraints_remain_distinct(self):
        base = canonical_intent_signature("mobile under 30000")
        branded = canonical_intent_signature("Samsung mobile under 30000")
        gaming = canonical_intent_signature("gaming mobile under 30000")
        self.assertNotEqual(base, branded)
        self.assertNotEqual(base, gaming)
        self.assertNotEqual(branded, gaming)

    def test_identity_fields_are_not_dropped_when_intent_is_enriched(self):
        base = parse_query("mobile under 30000")
        first = dict(base, model="Galaxy A56", ram_gb="8", storage_gb="128")
        second = dict(base, model="Galaxy S25", ram_gb="12", storage_gb="256")
        self.assertNotEqual(canonical_intent_signature(first), canonical_intent_signature(second))

    def test_named_models_do_not_share_a_budget_only_signature(self):
        galaxy = parse_query("exact model Galaxy F05 phone under 10000")
        iphone = parse_query("exact model iPhone 13 phone under 10000")
        self.assertEqual(galaxy["exact_model"], "galaxy f05")
        self.assertEqual(iphone["exact_model"], "iphone 13")
        self.assertNotEqual(canonical_intent_signature(galaxy), canonical_intent_signature(iphone))


if __name__ == "__main__":
    unittest.main()
