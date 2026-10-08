import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer
from reviewed_comparison_offers import REVIEWED_FILE
from multi_retailer_orchestrator import MultiRetailerOrchestrator

class RuntimeReviewedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.proof=json.loads(REVIEWED_FILE.read_text())
        self.product=CanonicalProduct(**self.proof['canonical_product'])
        self.offers=[RetailerOffer(**r) for r in self.proof['offers']]
        for o in self.offers: o.price=None; o.availability='unknown'
    def run_offers(self):
        return MultiRetailerOrchestrator(connector_manager=Mock(collect_offers=Mock(return_value=self.offers)),evidence_manager=Mock(collect_evidence=Mock(return_value=[]))).run(self.product)
    def test_matched_runtime_offers_reuse_reviewed_observations(self):
        result=self.run_offers()
        self.assertEqual([r['price'] for r in result['offers']],[r['price'] for r in self.proof['offers']])
        self.assertEqual([r['last_checked'] for r in result['offers']],[r['last_checked'] for r in self.proof['offers']])
    def test_wrong_variant_and_missing_connector_identity_fail_closed(self):
        self.product.variant='6GB/128GB'
        self.assertTrue(all(r['price'] is None for r in self.run_offers()['offers']))
        self.offers=[]
        self.assertEqual(self.run_offers()['offers'],[])
    def test_current_price_or_out_of_stock_is_not_replaced(self):
        self.offers[0].price=17001; self.offers[1].availability='out_of_stock'
        rows=self.run_offers()['offers']
        self.assertEqual(rows[0]['price'],17001); self.assertIsNone(rows[1]['price'])
    def test_expired_reviewed_prices_remain_noncomparable(self):
        rows=copy.deepcopy(self.proof['offers'])
        for r in rows:r['last_checked']='2000-01-01T00:00:00+00:00'
        with patch('reviewed_comparison_offers.merge_reviewed_offers',return_value={'offers':rows}):
            self.assertEqual(self.run_offers()['comparison']['comparable_offer_count'],0)

if __name__=='__main__':unittest.main()
