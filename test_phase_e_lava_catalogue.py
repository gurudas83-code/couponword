"""Existing catalogue importer must preserve the verified Lava brand."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from batch_product_importer import build_record
from product_engine import detect_brand

class LavaCatalogueTests(unittest.TestCase):
    def test_import_allocates_id_without_inventing_offer_facts(self):
        row=build_record([{'id':76}], 'B0HG9SZ7HD',
                         'Lava Virat V1 4GB RAM 64GB Storage', 'Mobiles')
        self.assertEqual((row['id'],row['brand'],row['asin']),
                         (77,'Lava','B0HG9SZ7HD'))
        for key in ('price','mrp','image','discount'):
            self.assertEqual(row[key],'')
    def test_compatible_accessory_does_not_claim_lava_brand(self):
        self.assertEqual(detect_brand('Case compatible with Lava Bold N2'), '')

if __name__=='__main__': unittest.main()
