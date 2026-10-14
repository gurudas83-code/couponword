import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from official_spec_extractor import extract_one, extract_vivo_selected_capacity
from product_evidence_store import variant_signature_from_specifications

class SelectedSkuTests(unittest.TestCase):
    url='https://shop.vivo.com/in/product/10339?skuId=19387'
    identity={'brand':'vivo','model':'T5x 5G','original_title':'vivo T5x 5G 6GB RAM 128GB Storage'}
    def run_extract(self,heading='T5x 5G 6GB+128GB Cyber Green',url=None,verified=True):
        specs={};extract_vivo_selected_capacity(BeautifulSoup('<h1>'+heading+'</h1>','html.parser'),specs,url or self.url,self.identity,verified);return specs
    def test_exact_selected_variant_binds_capacity(self):
        self.assertEqual(variant_signature_from_specifications(self.run_extract()),{'ram_gb':'6','storage_gb':'128'})
    def test_siblings_other_capacities_and_unverified_sources_stay_unknown(self):
        for heading in ('T5x 5G 8GB+128GB','T5x 5G 6GB+256GB','T4x 5G 6GB+128GB','T5x 5G 6GB+128GB / 8GB+256GB'):
            self.assertEqual(self.run_extract(heading),{})
        self.assertEqual(self.run_extract(verified=False),{})
        self.assertEqual(self.run_extract(url='https://example.com/in/product/10339?skuId=19387'),{})
        self.assertEqual(self.run_extract(url='https://shop.vivo.com/in/product/10339'),{})

    @patch("official_spec_extractor.collect_embedded_media_evidence")
    @patch("official_spec_extractor.fetch_page")
    def test_verified_vivo_store_sku_reaches_candidate_ready(self, fetch_page, media):
        html = '''<html><head><title>T5 Pro 5G</title></head><body>
        <h1>T5 Pro 5G 8GB+128GB Cosmic Black</h1>
        <script type="application/ld+json">{
          "@type":"Product","name":"T5 Pro 5G","sku":"19410",
          "brand":{"name":"vivo"},
          "description":"9020 mAh Battery | Snapdragon 7s Gen 4"
        }</script></body></html>'''
        fetch_page.return_value = (html, None, 200)
        media.return_value = {"product_image_count": 0, "excluded_ui_assets": 0}
        result = extract_one(
            {
                "product_id": "96",
                "title": "vivo T5 Pro 5G 8GB RAM 128GB Storage",
                "core_title": "vivo T5 Pro 5G",
                "brand": "vivo",
                "official_url": "https://shop.vivo.com/in/product/10344?skuId=19410",
                "status": "verified",
                "verified": True,
                "identity_decision": "verified",
                "_single_source_only": True,
            },
            {
                "brand": "vivo",
                "model": "T5 Pro 5G",
                "search_name": "vivo T5 Pro 5G",
                "original_title": "vivo T5 Pro 5G 8GB RAM 128GB Storage",
            },
        )
        self.assertEqual(
            variant_signature_from_specifications(result["specifications"]),
            {"ram_gb": "8", "storage_gb": "128"},
        )
        self.assertEqual(result["review"]["status"], "candidate_ready")
        self.assertGreaterEqual(result["page_identity_score"], 0.80)

if __name__=='__main__':unittest.main()
