import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python'))
from reviewed_comparison_offers import merge_reviewed_offers,REVIEWED_FILE
from retailer_contract import RetailerOffer
from multi_retailer_engine import compare_offers
class ReviewedComparisonTests(unittest.TestCase):
    def test_clean_deployment_has_two_exact_offers_without_refreshing_dates(self):
        proof=json.loads(REVIEWED_FILE.read_text())
        rows=merge_reviewed_offers({'offers':[]},'cw-mobile-82')['offers']
        self.assertEqual(len(rows),2)
        self.assertEqual([r['last_checked'] for r in rows],[r['last_checked'] for r in proof['offers']])
        compared=compare_offers([RetailerOffer(**r) for r in rows])
        self.assertEqual(compared['identity_matched_offer_count'],2)
    def test_wrong_variant_or_unregistered_sku_is_not_loaded(self):
        proof=json.loads(REVIEWED_FILE.read_text())
        proof['offers'][0]['variant']='6GB/128GB'
        proof['offers'][1]['retailer_product_id']='WRONG-SKU'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'proof.json';p.write_text(json.dumps(proof))
            self.assertEqual(merge_reviewed_offers({'offers':[]},'cw-mobile-82',p)['offers'],[])
    def test_newer_runtime_and_other_products_remain_unchanged(self):
        row=copy.deepcopy(json.loads(REVIEWED_FILE.read_text())['offers'][0]);row['last_checked']='2099-01-01T00:00:00+00:00'
        database={'offers':[row]};original=copy.deepcopy(database)
        result=merge_reviewed_offers(database,'cw-mobile-82')
        self.assertEqual(result['offers'][0],row);self.assertEqual(database,original)
        self.assertEqual(merge_reviewed_offers(database,'cw-mobile-83'),original)
    def test_static_offer_card_shows_absolute_observation_date(self):
        from multi_retailer_page_renderer import render_multi_retailer_section
        payload = json.loads((ROOT/'data/multi_retailer_public.json').read_text())
        product = next(p for p in payload['products'] if p['product_id']=='cw-mobile-82')
        rendered=render_multi_retailer_section({'id':82,'category':'Mobiles'}, {'cw-mobile-82':product})
        self.assertIn('08 Oct 2026',rendered)
        self.assertNotIn('checked recently',rendered)
        self.assertIn('Lowest observed price',rendered)

if __name__=='__main__':unittest.main()
