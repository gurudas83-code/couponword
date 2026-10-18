import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from official_source_resolver import (  # noqa: E402
    BRAND_DOMAINS,
    direct_official_product_search,
)
from product_evidence_store import variant_signature_from_specifications  # noqa: E402
from resolver_engine import compare_identity  # noqa: E402


class _Response:
    def __init__(self, url, text, status_code=200):
        self.url = url
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code


class PhaseDSourceRecoveryTests(unittest.TestCase):
    def test_combined_xiaomi_redmi_label_uses_existing_aliases(self):
        decision = compare_identity(
            "Xiaomi/Redmi Redmi 13 5G 6GB RAM 128GB Storage",
            "Redmi 13 5G Specs",
            "https://www.mi.com/in/product/redmi-13-5g/specs/",
            "Xiaomi/Redmi",
        )
        self.assertEqual(decision.decision, "verified")
        self.assertTrue(decision.brand_match)

    def test_expandable_or_multi_variant_capacity_is_unknown(self):
        self.assertEqual(
            variant_signature_from_specifications(
                {
                    "memory": {
                        "value": (
                            "RAM: 6GB | 8GB Internal memory: 128GB; "
                            "up to 1TB expandable storage"
                        )
                    }
                }
            ),
            {},
        )
        self.assertEqual(
            variant_signature_from_specifications(
                {
                    "storage_ram": {
                        "value": "8GB+256GB, 12GB+256GB, 12GB+512GB"
                    }
                }
            ),
            {},
        )

    def test_known_manufacturer_paths_are_bounded_and_identity_checked(self):
        pages = {
            "https://www.mi.com/in/product/redmi-13-5g/specs/":
                "<title>Redmi 13 5G Specs</title>",
            "https://www.po.co/global/product/poco-x7-pro/specs/":
                "<title>POCO X7 Pro Specs</title>",
            "https://www.motorola.in/smartphones-motorola-edge-60-fusion/p?skuId=491":
                "<title>Motorola Edge 60 Fusion</title>",
        }

        def fake_get(url, **_kwargs):
            if url in pages:
                return _Response(url, pages[url])
            return _Response(url, "", 404)

        with patch("official_source_resolver.requests.get", side_effect=fake_get):
            cases = (
                (
                    "Redmi 13 5G",
                    "Xiaomi/Redmi",
                    ["mi.com", "xiaomi.com"],
                    "https://www.mi.com/in/product/redmi-13-5g/specs/",
                ),
                (
                    "X7 Pro 5G",
                    "POCO",
                    BRAND_DOMAINS["poco"],
                    "https://www.po.co/global/product/poco-x7-pro/specs/",
                ),
                (
                    "Edge 60 Fusion",
                    "Motorola",
                    BRAND_DOMAINS["motorola"],
                    "https://www.motorola.in/smartphones-motorola-edge-60-fusion/p?skuId=491",
                ),
            )
            for title, brand, domains, expected_url in cases:
                results = direct_official_product_search(
                    title, brand, domains, max_results=5
                )
                self.assertIn(expected_url, {item["url"] for item in results})


if __name__ == "__main__":
    unittest.main()
