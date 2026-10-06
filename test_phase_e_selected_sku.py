import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from official_spec_extractor import extract_vivo_selected_capacity
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

if __name__=='__main__':unittest.main()
