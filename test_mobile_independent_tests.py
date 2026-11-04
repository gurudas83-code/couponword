import json
import unittest
from pathlib import Path
from python.mobile_research_catalogue import build_public_catalogue, _apply_independent_tests

ROOT = Path(__file__).resolve().parent

class IndependentTests(unittest.TestCase):
    def test_measurements_remain_context_only(self):
        ledger = json.loads((ROOT / 'data/mobile_independent_test_evidence.json').read_text())
        cards = [{'model_key': item['model_key']} for item in ledger['models']]
        _apply_independent_tests(ROOT, cards)
        self.assertEqual(len(cards), 6)
        self.assertEqual(sum(len(c['independent_tests']) for c in cards), 16)
        self.assertTrue(all(m['ranking_eligible'] is False for c in cards for m in c['independent_tests']))
        self.assertTrue(all(m['observed_at'] is None for c in cards for m in c['independent_tests']))
        poco = next(c for c in cards if c['model_key'] == 'poco|x7 pro')
        self.assertIn('6000mAh', poco['independent_test_limitation'])
        self.assertIn('6550mAh', poco['independent_test_limitation'])
        games = [m for c in cards for m in c['independent_tests'] if m['category'] == 'gaming']
        self.assertEqual(sum(m['test_version'] is None for m in games), 3)
        self.assertNotEqual(games[3]['test_version'], games[5]['test_version'])

    def test_catalogue_attaches_only_exact_model_keys(self):
        payload = build_public_catalogue(ROOT)
        cards = payload['model_cards']
        attached = [c for c in cards if c.get('independent_tests')]
        self.assertEqual(len(attached), 6)
        self.assertFalse(any(c.get('independent_tests') for c in cards if 'pro' in c['model_key'] and c['model_key'] != 'poco|x7 pro'))

if __name__ == '__main__':
    unittest.main()
