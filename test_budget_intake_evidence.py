"""A dated budget quote must match physical RAM/storage and stay non-live."""
import copy
import json
import unittest
from unittest.mock import patch
from python.india_recent_eight_import import SOURCE, build_recent, _attach_reviewed_budget


class BudgetIntakeEvidenceTests(unittest.TestCase):
    def test_a5_exact_physical_memory_and_non_live_reference(self):
        card = next(c for c in build_recent()['model_cards'] if c['model_key'] == 'redmi|a5')
        ref = card['research_budget_reference']
        self.assertEqual((ref['ram_gb'], ref['storage_gb'], ref['reference_price_inr']), (3, 64, 6999))
        self.assertFalse(ref['live_offer'])
        self.assertEqual(ref['ranking_weight'], 0)
        self.assertFalse(card['india_identity_evidence']['purchase_eligible'])
        self.assertFalse(card['api_probe_eligible'])

    def test_rejects_wrong_memory_unavailable_future_or_unreviewed_retailer(self):
        item = next(x for x in json.loads(SOURCE.read_text())['models'] if x['name'] == 'Redmi A5')
        for changes in ({'ram_gb': 7}, {'stock_indication': 'OUT_OF_STOCK'},
                        {'checked_at': '2099-01-01'}, {'reference_price_inr': 0},
                        {'source_url': 'https://www.bigbasket.com.evil.example/pd/phone/'},
                        {'source_url': 'https://attacker@www.bigbasket.com/pd/phone/'}):
            broken = copy.deepcopy(item)
            broken['dated_price_reference'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                _attach_reviewed_budget({'manufacturer_page': item['source']}, broken)

    def test_named_art_cannot_be_reused_for_another_model(self):
        from pathlib import Path
        from python.mobile_research_catalogue import apply_representative_illustrations
        ROOT = Path(__file__).resolve().parent
        card = {'model_key': 'google|pixel 10a', 'image_status': 'PLACEHOLDER'}
        with patch('python.mobile_research_catalogue._read_json', return_value={
                card['model_key']: '/assets/phone-illustrations/oppo-a5x-ai-front.webp'}):
            with self.assertRaisesRegex(ValueError, 'Cross-model'):
                apply_representative_illustrations(ROOT, [card])
