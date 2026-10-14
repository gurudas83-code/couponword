import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from python import retail_price_evidence as prices
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from python.official_source_resolver import direct_official_product_search


class ManufacturerPriceAdapterTests(unittest.TestCase):
    def test_only_product_paths_are_allowed(self):
        self.assertTrue(prices.retailer_host_allowed("https://www.oneplus.in/15"))
        self.assertTrue(prices.retailer_host_allowed(
            "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/buy/"
        ))
        self.assertTrue(prices.retailer_host_allowed(
            "https://shop.vivo.com/in/product/10344?skuId=19410"
        ))
        self.assertTrue(prices.retailer_host_allowed(
            "https://shop.lavamobiles.com/products/lava-agni-4?variant=53290002055478"
        ))
        self.assertFalse(prices.retailer_host_allowed(
            "https://shop.vivo.com/in/product/10344"
        ))
        self.assertFalse(prices.retailer_host_allowed(
            "https://shop.lavamobiles.com/collections/all"
        ))
        self.assertFalse(prices.retailer_host_allowed("https://www.oneplus.in/support"))
        self.assertFalse(prices.retailer_host_allowed("https://news.samsung.com/in/"))

    @patch("python.retail_price_evidence.requests.get")
    def test_first_party_store_jsonld_price_and_stock(self, get):
        html = '''<script type="application/ld+json">
        {"@type":"Product","name":"T5 Pro 5G 8GB+128GB",
         "offers":{"@type":"Offer","price":"41999","priceCurrency":"INR",
         "availability":"https://schema.org/InStock"}}
        </script>'''
        get.return_value = SimpleNamespace(
            status_code=200,
            url="https://shop.vivo.com/in/product/10344",
            text=html,
        )
        result = prices.fetch_structured_price(
            "https://shop.vivo.com/in/product/10344?skuId=19410"
        )
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["price"], 41999.0)
        self.assertEqual(result["availability"], "in_stock")

    @patch("python.official_source_resolver.requests.get")
    def test_capacity_free_model_slugs_are_probed(self, get):
        get.return_value = SimpleNamespace(status_code=404, url="", text="")
        direct_official_product_search(
            "Redmi Note 17 Pro Max 5G 8GB RAM 256GB Storage",
            "Redmi",
            ["mi.com"],
        )
        direct_official_product_search(
            "vivo T5x 5G 8GB RAM 256GB Storage",
            "vivo",
            ["vivo.com"],
        )
        urls = [call.args[0] for call in get.call_args_list]
        self.assertIn(
            "https://www.mi.com/in/product/redmi-note-17-pro-max-5g/",
            urls,
        )
        self.assertIn(
            "https://www.vivo.com/in/products/t5x",
            urls,
        )

    @patch("python.retail_price_evidence.requests.get")
    def test_jsonld_price_and_availability_are_first_party_evidence(self, get):
        html = '''<script type="application/ld+json">
        {"@type":"Product","name":"OnePlus 15 12GB 256GB",
         "offers":{"@type":"Offer","price":"85999","priceCurrency":"INR",
         "availability":"https://schema.org/InStock"}}
        </script>'''
        get.return_value = SimpleNamespace(status_code=200, url="https://www.oneplus.in/15", text=html)
        result = prices.fetch_structured_price("https://www.oneplus.in/15")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["price"], 85999.0)
        self.assertEqual(result["availability"], "in_stock")

    @patch("python.retail_price_evidence.requests.get")
    def test_missing_price_does_not_use_page_mentions(self, get):
        html = '<meta name="description" content="OnePlus 15 from ₹84,999">'
        get.return_value = SimpleNamespace(status_code=200, url="https://www.oneplus.in/15", text=html)
        result = prices.fetch_structured_price("https://www.oneplus.in/15")
        self.assertIsNone(result["price"])
        self.assertNotEqual(result["status"], "verified")


if __name__ == "__main__":
    unittest.main()
