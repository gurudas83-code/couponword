"""Saving an unpromoted phone must never manufacture a canonical ID."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import mobile_intelligence_repository as repository
from mobile_product_dna import MobileProductDNA


class PrivateMobileDNATests(unittest.TestCase):
    def test_unresolved_record_remains_unresolved_when_saved_and_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "private_mobile_repository.json"
            with patch.object(repository, "REPOSITORY_FILE", target):
                unresolved = MobileProductDNA(product_id="research-1")
                self.assertTrue(repository.save_mobile_dna(unresolved)[0])
                self.assertIsNone(repository.get_mobile_record("research-1")["canonical_product_id"])
                self.assertIsNone(repository.get_mobile_dna_dict("research-1")["canonical_product_id"])

                # An explicit, already established canonical ID is retained.
                resolved = MobileProductDNA(
                    product_id="research-1", canonical_product_id="cw-mobile-10"
                )
                self.assertTrue(repository.save_mobile_dna(resolved)[0])
                self.assertEqual(repository.get_mobile_record("research-1")["canonical_product_id"], "cw-mobile-10")

                # A later record without proof must not inherit the old ID.
                self.assertTrue(repository.save_mobile_dna(unresolved)[0])
                self.assertIsNone(repository.get_mobile_record("research-1")["canonical_product_id"])


if __name__ == "__main__":
    unittest.main()
