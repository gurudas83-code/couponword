import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from official_spec_extractor import extract_oneplus_15_meta_specs, page_identity_score


class OnePlusExtractorTests(unittest.TestCase):
    html = """
    <html><head><title>OnePlus 15</title>
    <meta name="keywords" content="OnePlus 15, Snapdragon 8 Elite Gen 5, 165Hz display, 7300 mAh battery, triple 50MP camera, 4K 120FPS Dolby Vision, OxygenOS 16">
    </head><body></body></html>
    """

    def test_exact_oneplus_15_meta_is_source_specific(self):
        specs = {}
        count = extract_oneplus_15_meta_specs(
            BeautifulSoup(self.html, "html.parser"),
            "https://www.oneplus.in/15",
            specs,
        )
        self.assertEqual(count, 6)
        self.assertEqual(specs["processor"]["source"], "oneplus_official_meta")
        self.assertEqual(specs["battery_capacity"]["value"], "7300 mAh")
        self.assertEqual(specs["display_refresh"]["value"], "165Hz")

    def test_15r_and_other_manufacturers_are_not_accepted(self):
        for url in (
            "https://www.oneplus.in/15r",
            "https://www.samsung.com/in/15",
        ):
            with self.subTest(url=url):
                specs = {}
                self.assertEqual(
                    extract_oneplus_15_meta_specs(
                        BeautifulSoup(self.html, "html.parser"), url, specs
                    ),
                    0,
                )

    def test_model_identity_score_has_strict_numeric_model(self):
        self.assertGreaterEqual(
            page_identity_score(
                "OnePlus 15", "OnePlus 15", "https://www.oneplus.in/15"
            ),
            0.80,
        )
        self.assertLess(
            page_identity_score(
                "OnePlus 15", "OnePlus 15R", "https://www.oneplus.in/15r"
            ),
            0.80,
        )


if __name__ == "__main__":
    unittest.main()
