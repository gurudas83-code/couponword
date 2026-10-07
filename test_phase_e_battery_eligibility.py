import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from intent_engine import parse_query
from weighted_fit_engine import calculate_product_fit
from product_fit_signal_builder import smartphone_battery_signal
class BatteryEligibilityTests(unittest.TestCase):
    def profile(self,intent,text):
        signals={key:{'match':1.0,'status':'verified','reason':'fixture'} for key in intent['priority_weights']}
        signals['battery']=smartphone_battery_signal(text)
        return {'price':9000,'brand':'Lava','fit_signals':signals}
    def test_best_battery_rejects_proxy_but_keeps_score_threshold(self):
        for budget in ('20k','30k','50k'):
            intent=parse_query('best battery under '+budget)
            result=calculate_product_fit(self.profile(intent,'7000mAh; 750 hours standby'),intent)
            self.assertGreaterEqual(result['fit_percent'],50)
            self.assertFalse(result['eligible'])
            self.assertTrue(any('active-use endurance' in f for f in result['hard_constraint_failures']))
            self.assertTrue(calculate_product_fit(self.profile(intent,'Youtube Playback Time 810min; 6000mAh'),intent)['eligible'])
    def test_generic_and_parent_phone_queries_keep_capacity_proxy(self):
        for query in ('mobile under 15000','phone for parents under 20000','headphones best battery under 10000'):
            intent=parse_query(query)
            self.assertNotIn('active_battery_endurance',intent['hard_constraints'])
    def test_no_duration_or_partial_charge_cannot_claim_endurance(self):
        intent=parse_query('best battery under 20000')
        for text in ('750 hours standby','Video Playback 10 hours; 50% charge left;7000mAh'):
            self.assertFalse(calculate_product_fit(self.profile(intent,text),intent)['eligible'])
if __name__=='__main__':unittest.main()
