"""Technical-only publication contract without changing the source database."""
import json
import tempfile
import unittest
from pathlib import Path

from python.technical_niche_publication import (
    REVIEWED_TECH_COUNT,
    REVIEWED_TECH_IDS,
    TECH_CATEGORIES,
    publish_tech_subset,
    select_tech_products,
)

ROOT = Path(__file__).resolve().parent


class TechnicalNichePublicationTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "coupons.json").read_text(encoding="utf-8"))

    def test_strict_tech_allowlist_and_no_accidental_nontech(self):
        selected = select_tech_products(self.source)
        self.assertEqual(len(selected), 65)
        self.assertEqual(len(REVIEWED_TECH_IDS), REVIEWED_TECH_COUNT)
        self.assertEqual({int(p["id"]) for p in selected}, REVIEWED_TECH_IDS)
        self.assertTrue(all(p["category"] in TECH_CATEGORIES for p in selected))
        self.assertFalse(set([1, 3, 4, 7, 8, 12, 16, 17, 18, 22, 27, 35, 40, 43, 44, 45,
                             46, 47, 48, 49, 50, 51, 61, 62, 63, 64, 65, 66, 67, 68, 70, 71])
                         & {int(p["id"]) for p in selected})

    def test_source_unchanged_and_public_subset_tech_only(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            initial = (ROOT / "coupons.json").read_bytes()
            result = publish_tech_subset(target, self.source)
            self.assertEqual((ROOT / "coupons.json").read_bytes(), initial)
            published = json.loads((target / "coupons.json").read_text(encoding="utf-8"))
            self.assertEqual(len(published), 65)
            self.assertEqual(result["source_records"], 105)
            self.assertEqual(result["excluded_non_tech_records"], 40)
            self.assertEqual(result["published_tech_records"], 65)

    def test_reject_new_unreviewed_products_and_category_relabel(self):
        changed = [dict(p) for p in self.source]
        for p in changed:
            if int(p["id"]) == 2:
                p["category"] = "Fashion"
        with self.assertRaisesRegex(ValueError, "category changed"):
            select_tech_products(changed)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            select_tech_products(self.source + [dict(self.source[0])])

    def test_clean_homepage_retains_technical_entrypoints(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        for route in ("/phones/", "/compare/", "/accessories/earbuds-20/",
                      "/tvs/india-20/", "/guides/phone-budget-guides/"):
            self.assertIn('href="' + route + '"', content)
        for legacy in ('id="hot-deals"', 'id="categories"', 'id="legacyCategories"',
                       'id="catalogueDiscovery"', 'id="under-budget"',
                       'data-quick="Fashion"', 'data-quick="Home"',
                       'data-quick="Toys"'):
            self.assertNotIn(legacy, content)
        for hook in ('id="mobileResearchSearch"', 'id="mobileResearchCatalogue"',
                     'id="shoppingBrainCard"', 'id="researchCategories"'):
            self.assertIn(hook, content)

    def test_public_pages_are_tech_only_if_built(self):
        public = ROOT / "public"
        if not public.exists():
            self.skipTest("Artifact tests run after the build")
        selected = select_tech_products(self.source)
        ids = {int(product["id"]) for product in selected}
        public_json = json.loads((public / "coupons.json").read_text(encoding="utf-8"))
        self.assertEqual({int(row["id"]) for row in public_json}, ids)
        from python.build_product_pages import page_dir
        expected_slugs = {page_dir(row).name for row in selected}
        actual_slugs = {path.parent.name for path in (public / "products").glob("*/index.html")}
        self.assertEqual(actual_slugs, expected_slugs)
        for item in public_json:
            self.assertNotIn(item.get("category"), {"Fashion", "Home", "Toys", "Beauty", "Fitness", "Footwear"})


if __name__ == "__main__":
    unittest.main()
