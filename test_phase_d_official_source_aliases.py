import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from official_source_resolver import BRAND_DOMAINS, normalize_brand


class OfficialSourceAliasTests(unittest.TestCase):
    def test_research_brands_have_approved_official_domains(self):
        expected = {
            "OPPO": "oppo",
            "POCO": "poco",
            "iQOO": "iqoo",
            "Google": "google",
            "Infinix": "infinix",
            "Tecno": "tecno",
            "CMF": "cmf",
            "Xiaomi/Redmi": "xiaomiredmi",
        }
        for label, key in expected.items():
            self.assertEqual(normalize_brand(label), key)
            self.assertTrue(BRAND_DOMAINS.get(key), label)

    def test_alias_domains_are_manufacturer_domains(self):
        self.assertIn("mi.com", BRAND_DOMAINS["poco"])
        self.assertIn("vivo.com", BRAND_DOMAINS["iqoo"])
        self.assertIn("store.google.com", BRAND_DOMAINS["google"])
        self.assertIn("in.nothing.tech", BRAND_DOMAINS["cmf"])


if __name__ == "__main__":
    unittest.main()
