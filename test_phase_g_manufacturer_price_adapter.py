import unittest
from types import SimpleNamespace
from unittest.mock import patch

from python import retail_price_evidence as prices


class ManufacturerPriceAdapterTests(unittest.TestCase):
    def test_only_product_paths_are_allowed(self):
        self.assertTrue(prices.retailer_host_allowed("https://www.oneplus.in/15"))
        self.assertTrue(prices.retailer_host_allowed(
            "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/buy/"
        ))
        self.assertFalse(prices.retailer_host_allowed("https://www.oneplus.in/support"))
        self.assertFalse(prices.retailer_host_allowed("https://news.samsung.com/in/"))

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
