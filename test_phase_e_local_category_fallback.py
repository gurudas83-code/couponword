import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import market_discovery as discovery

class LocalCategoryFallbackTests(unittest.TestCase):
    def search(self, query, category='smartphone'):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [
                {'title': 'Lava Bold N2 4GB RAM 64GB Storage', 'link': 'https://www.amazon.in/dp/B0GL1WGHJX', 'category': 'Mobiles', 'asin':'B0GL1WGHJX'},
                {'title': 'Lava Bold N2 Lite 3GB RAM 64GB Storage', 'link': 'https://www.amazon.in/dp/B0GPXTY8V5', 'category': 'Mobiles', 'asin':'B0WRONG123'},
                {'title': 'Unrelated gadget', 'link': 'https://www.amazon.in/dp/B000000001', 'category': 'Electronics'},
            ]
            (root / 'coupons.json').write_text(json.dumps(rows), encoding='utf-8')
            with patch.object(discovery, 'ROOT', root):
                return discovery.local_known_product_fallback(query=query, category=category, max_results=20)

    def test_generic_mobile_queries_retain_category_members(self):
        for query in ('smartphone under 10000 India', 'mobile under 15000 India'):
            with self.subTest(query=query):
                rows = self.search(query)
                self.assertEqual(len(rows), 2)
                self.assertTrue(all(row['provider'] == 'local_coupon_catalogue' for row in rows))
                self.assertTrue(all('verified' not in row for row in rows))

    def test_only_url_bound_catalogue_asin_is_forwarded(self):
        rows=self.search('mobile under 15000')
        self.assertEqual(rows[0]['asin'],'B0GL1WGHJX')
        self.assertIsNone(rows[1]['asin'])

    def test_explicit_brand_or_variant_does_not_gain_category_only_match(self):
        for query in ('Samsung phone under 10000', 'smartphone 8GB 256GB', 'Moto G45'):
            with self.subTest(query=query):
                self.assertEqual(self.search(query), [])

    def test_category_expansion_does_not_apply_to_other_categories(self):
        self.assertEqual(self.search('smartphone under 10000', 'laptop'), [])

if __name__ == '__main__':
    unittest.main()
