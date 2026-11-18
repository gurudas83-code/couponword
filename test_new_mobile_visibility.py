"""New India phones must be discoverable on the home page and in public research.

This does not certify live retailer prices, exact SKUs or Google indexing.
"""
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.india_missing_eight_pages import import_eight
from python.india_recent_eight_import import APPROVED, HUB, MODE, PUBLIC_DATA_NAME, build_recent

ROOT = Path(__file__).resolve().parent
THREE = {"samsung|galaxy f70 5g", "redmi|redmi 17c 5g", "realme|p4s lite"}


class NewMobileVisibleTests(unittest.TestCase):
    def test_unique_251_models_with_strict_research_gates(self):
        core = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        market = import_eight()
        recent = build_recent()
        self.assertEqual((len(core["model_cards"]), len(market["model_cards"]),
                          len(recent["model_cards"])), (232, 8, 13))
        keys = [c["model_key"] for group in (core, market, recent) for c in group["model_cards"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 251)
        self.assertEqual(len(APPROVED), 13)
        self.assertTrue(THREE.issubset({c["model_key"] for c in recent["model_cards"]}))
        for card in recent["model_cards"]:
            self.assertTrue(card["recent_source_intake"])
            self.assertEqual(card["status"], "RESEARCH_ONLY")
            self.assertIsNone(card["photo"])
            self.assertFalse(card["verified_retailer_links"])
            self.assertNotIn("price", card)
            self.assertNotIn("stock", card)

    def test_homepage_and_client_show_new_models_not_just_verified_launches(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.assertIn('id="mobileResearchNew"', home)
        self.assertIn('href="' + HUB + '"', home)
        self.assertIn("mobileResearchNewCount", home)
        self.assertIn("india_recent_manufacturer_research.json", js)
        self.assertIn("card.market_intake === true", js)
        self.assertIn('Show all ', js)
        function = js.split("  function renderNewNoteworthy() {", 1)[1].split(
            '\n  fetch("/data/mobile_research_preview.json"', 1
        )[0]
        self.assertNotIn('card.status === "OFFICIAL_VERIFIED"', function)
        self.assertNotIn('launch_date_india', function)

    def test_built_hub_and_data_have_usable_discovery_paths(self):
        public = ROOT / "public"
        if not (public / "sitemap.xml").exists():
            self.skipTest("Run after approved public build")
        payload = json.loads((public / "data" / PUBLIC_DATA_NAME).read_text(encoding="utf-8"))
        self.assertEqual(payload["mode"], MODE)
        self.assertEqual(len(payload["model_cards"]), 13)
        html = (public / HUB.lstrip("/") / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://coupon-world.in' + HUB + '"', html)
        for name in ("Galaxy F70 5G", "17C 5G", "P4s Lite"):
            self.assertIn(name, html)
        urls = [node.text for node in ET.parse(public / "sitemap.xml").getroot().iter()
                if node.tag.endswith("}loc")]
        self.assertIn("https://coupon-world.in" + HUB, urls)
        self.assertFalse(any("recent-source|" in url for url in urls))


if __name__ == "__main__":
    unittest.main()