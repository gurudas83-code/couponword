import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from lava_support_evidence import add_lava_support_evidence, SUPPORT_URL

POLICY = '<p>We will provide quarterly security updates for two years after the launch of a model and three years for flagship Agni Series models.</p>'
def page(model='Bold N2', extra=''):
    return POLICY + '<div class="tab-content">' + extra + '<div class="product-model-container"><h2>' + model + '</h2><div class="col"><span>Launch Date</span><h4>Feb-26</h4></div></div></div>'
class LavaSupportTests(unittest.TestCase):
    def setUp(self):
        self.output = {'resolver_verified': True, 'review': {'status': 'candidate_ready'}, 'official_url': 'https://www.lavamobiles.com/smartphones/bold-n2', 'specifications': {'ram': {'value': '4GB'}, 'internal_memory': {'value': '64GB'}}}
        self.identity = {'model': 'Bold N2', 'brand': 'Lava', 'original_title': 'Lava Bold N2 4GB RAM 64GB Storage'}
        self.html = '<a href="/software-update-center">Android updates</a>'
    def run_policy(self, content=None, date='2026-09-30T01:00:00+00:00'):
        self.fetch = Mock(return_value=(content or page(), None, 200))
        return add_lava_support_evidence(self.output, self.identity, self.html, self.fetch, date)
    def test_exact_model_policy_has_provenance(self):
        self.assertTrue(self.run_policy())
        fact = self.output['specifications']['software_security_support']
        self.assertEqual(fact['source_url'], SUPPORT_URL)
        self.assertEqual(fact['identity_match']['variant'], {'ram_gb': '4', 'storage_gb': '64'})
        self.assertNotIn('Android 17', fact['value'])
        self.fetch.assert_called_once_with(SUPPORT_URL)
    def test_sibling_or_duplicate_rows_rejected(self):
        self.assertFalse(self.run_policy(page('Bold N2 5G')))
        self.assertFalse(self.run_policy(page()+page()))
    def test_wrong_variant_and_unverified_source_do_not_fetch(self):
        self.identity['original_title'] = 'Lava Bold N2 6GB RAM 128GB Storage'
        self.assertFalse(self.run_policy()); self.fetch.assert_not_called()
        self.identity['original_title'] = 'Lava Bold N2 4GB RAM 64GB Storage'
        self.output['resolver_verified'] = False
        self.assertFalse(self.run_policy()); self.fetch.assert_not_called()
    def test_missing_link_or_policy_stays_unknown(self):
        self.html = '<a href="https://other.example/software-update-center">updates</a>'
        self.assertFalse(self.run_policy()); self.fetch.assert_not_called()
        self.html = '<a href="/software-update-center">updates</a>'
        self.assertFalse(self.run_policy(page().replace(POLICY, '')))
    def test_expiry_and_eol_fail_closed(self):
        self.assertFalse(self.run_policy(date='2028-02-01T00:00:00+00:00'))
        self.assertFalse(self.run_policy(page(extra='End-of-Life Models')))

if __name__ == '__main__': unittest.main()
