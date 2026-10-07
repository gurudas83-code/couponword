import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
import shopping_intelligence_pipeline as p
import retailer_product_registry as registry

class CanonicalSelectionTests(unittest.TestCase):
    def item(self,asin,title,brand='Lava',fit=55):
        return {'candidate':{'candidate_id':asin,'title':title},'profile':{'asin':asin,'brand':brand},'fit_assessment':{'eligible':True,'fit_percent':fit}}

    def test_unmapped_sibling_cannot_displace_catalogued_variant(self):
        unknown=self.item('B0GPY2KG7B','Lava Bold N2 Lite Nilgiri Blue 3GB RAM 64GB Storage',fit=60)
        title=next(x['title'] for x in json.loads((Path(__file__).parent/'coupons.json').read_text(encoding='utf-8-sig')) if x.get('asin')=='B0GPXTY8V5')
        known=self.item('B0GPXTY8V5',title,fit=51)
        items=[unknown,known];before=copy.deepcopy(items);failures=[]
        self.assertEqual(p.catalogued_recommendation_candidates(items,failures),[known])
        self.assertEqual(items,before)
        self.assertEqual(failures[0]['stage'],'canonical_identity')

    def test_registry_does_not_rescue_wrong_variant(self):
        wrong=self.item('B0GPXTY8V5','Lava Bold N2 Lite 8GB RAM 256GB Storage')
        self.assertEqual(p.catalogued_recommendation_candidates([wrong],[]),[])

    def test_catalogue_shortage_is_not_padded(self):
        unknown=self.item('B000000000','Lava Bold N2 Lite 3GB RAM 64GB Storage')
        failures=[]
        self.assertEqual(p.catalogued_recommendation_candidates([unknown],failures),[])
        self.assertEqual(len(failures),1)

    def test_duplicate_owner_remains_blocked(self):
        known=self.item('B0GPXTY8V5','Lava Bold N2 Lite 3GB RAM 64GB Storage')
        corrupted=copy.deepcopy(registry.load_registry())
        corrupted['products']['cw-mobile-999']={'amazon':{'retailer_product_id':'B0GPXTY8V5'}}
        with patch.object(registry,'load_registry',return_value=corrupted):
            self.assertEqual(p.catalogued_recommendation_candidates([known],[]),[])

if __name__=='__main__':unittest.main()
