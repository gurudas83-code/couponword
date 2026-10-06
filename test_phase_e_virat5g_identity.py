import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
import official_spec_extractor as extractor
class Virat5GIdentityTests(unittest.TestCase):
    def extract(self, title='Virat V1 5G', url='https://www.lavamobiles.com/smartphones/virat-v1-5g', ram='4GB', verified=True):
        html=f'<html><head><title>{title}</title></head><body><table><tr><th>RAM</th><td>{ram}</td></tr><tr><th>Internal Memory</th><td>64GB</td></tr></table></body></html>'
        identity={'brand':'Lava','model':'Virat V1 5G','search_name':'Lava Virat V1 5G','original_title':'Lava Virat V1 5G 4GB RAM 64GB Storage'}
        with patch.object(extractor,'fetch_page',return_value=(html,None,200)):
            return extractor.extract_one({'verified':verified,'identity_decision':'verified','official_url':url,'_single_source_only':True},identity)
    def test_exact_official_5g_model_and_capacity(self):
        result=self.extract()
        self.assertEqual(result['page_identity_score'],1.0)
        self.assertEqual(result['identity_match_mode'],'verified_official_model_exact_capacity')
    def test_sibling_host_capacity_and_unverified_do_not_inherit_exception(self):
        for kwargs in ({'title':'Virat V1'}, {'url':'https://www.lavamobiles.com/smartphones/virat-v1'}, {'url':'https://example.com/smartphones/virat-v1-5g'}, {'ram':'8GB'}, {'verified':False}):
            with self.subTest(kwargs=kwargs):
                self.assertNotEqual(self.extract(**kwargs).get('identity_match_mode'),'verified_official_model_exact_capacity')
if __name__=='__main__':unittest.main()
