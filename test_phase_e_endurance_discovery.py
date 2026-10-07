import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from market_discovery import active_endurance_discovery_priority
class VerifiedEnduranceDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.row={'asin':'B0HCNQPXRY','url':'https://www.amazon.in/dp/B0HCNQPXRY','title':'Lava Virat V1 5G 4GB RAM 64GB Storage'}
        self.record={'asin':'B0HCNQPXRY','brand':'Lava','model':'Virat V1 5G','variant_signature':{'ram_gb':'4','storage_gb':'64'},'resolver_verified':True,'fetch_status':'success','page_identity_score':1.0,'review':{'status':'candidate_ready'},'specifications':{'youtube_playback_time':{'value':'810mins'},'ram':{'value':'4GB'},'internal_memory':{'value':'64GB'}},'features':[]}
    def priority(self,row=None,record=None):return active_endurance_discovery_priority(row or self.row,{'records':[record or self.record]})
    def test_exact_known_duration_gets_priority_without_mutating_row(self):
        before=copy.deepcopy(self.row);self.assertEqual(self.priority(),1);self.assertEqual(self.row,before)
    def test_sibling_capacity_wrong_asin_and_unverified_are_not_prioritized(self):
        for change in ({'title':'Lava Virat V1 4GB RAM 64GB Storage'},{'title':'Lava Virat V1 5G 8GB RAM 128GB Storage'},{'url':'https://www.amazon.in/dp/B0WRONG123'}):
            with self.subTest(change=change):self.assertEqual(self.priority(row=dict(self.row,**change)),0)
        self.assertEqual(self.priority(record=dict(self.record,resolver_verified=False)),0)
    def test_proxy_and_partial_charge_do_not_get_priority(self):
        for text in ('6000mAh;Standby750hours','Video playback10hours;50% charge left'):
            record=copy.deepcopy(self.record);record['specifications']={'battery':{'value':text}}
            self.assertEqual(self.priority(record=record),0)
if __name__=='__main__':unittest.main()
