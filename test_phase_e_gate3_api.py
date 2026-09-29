"""Gate 3 cannot pass just because the endpoint returns HTTP 200."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from phase_e_gate3_api import check_payload, check_repeat
from product_fit_signal_builder import smartphone_battery_signal


class Gate3APITests(unittest.TestCase):
    def payload(self):
        # Deliberately unresolved fixture, never persisted to a catalogue.
        title = 'Redmi 13 5G (8GB RAM, 128GB Storage)'
        battery = smartphone_battery_signal('5000mAh; 340 hours standby')
        pick = {'asin': 'B0F1N8B7Z4', 'brand': 'Redmi', 'title': title,
                'price': 19000, 'fit_percent': 60, 'canonical_product_id': None,
                'identity_evidence': {'status': 'canonical_unresolved', 'source_title': title,
                                      'variant': {'ram_gb': '8', 'storage_gb': '128'}},
                'battery_evidence': battery}
        pick['provenance'] = {'price_evidence': {'verified': True, 'price': 19000,
                                               'source_url': 'https://www.amazon.in/dp/B0F1N8B7Z4'}}
        row = {'profile_asin': pick['asin'], 'title': title, 'features': ['5000mAh; 340 hours standby'],
               'battery_evidence': battery,
               'criteria': [{'criterion': 'battery', 'match_score': battery['match']}]}
        return {'intent': {'preferred': ['good_battery']}, 'recommendations': [pick], 'fit_diagnostics': [row]}

    def check(self, payload):
        with patch('phase_e_gate3_api.find_catalogued_mobile_id', return_value=None):
            return check_payload(payload, 200, 20000)

    def test_no_false_pass_for_empty_success(self):
        self.assertEqual(self.check({})['status'], 'INCOMPLETE')

    def test_unresolved_identity_and_capacity_only_are_explicit_gaps(self):
        result = self.check(self.payload())
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertTrue(any('endurance unverified' in gap for gap in result['coverage_gaps']))

    def test_fabricated_canonical_or_variant_is_a_failure(self):
        for field in ('canonical', 'variant'):
            payload = self.payload()
            if field == 'canonical':
                payload['recommendations'][0]['canonical_product_id'] = 'market-01'
            else:
                payload['recommendations'][0]['identity_evidence']['variant']['ram_gb'] = '12'
            self.assertEqual(self.check(payload)['status'], 'FAIL')

    def test_wrong_budget_brand_duplicate_and_battery_score_are_failures(self):
        for defect in ('budget', 'brand', 'duplicate', 'battery'):
            payload = self.payload()
            pick = payload['recommendations'][0]
            if defect == 'budget':
                pick['price'] = 21000
            elif defect == 'brand':
                with patch('phase_e_gate3_api.find_catalogued_mobile_id', return_value=None):
                    self.assertEqual(check_payload(payload, 200, 20000, 'samsung')['status'], 'FAIL')
                continue
            elif defect == 'duplicate':
                payload['recommendations'].append(copy.deepcopy(pick))
            else:
                payload['fit_diagnostics'][0]['criteria'][0]['match_score'] = 1.0
            self.assertEqual(self.check(payload)['status'], 'FAIL')

    def test_expired_and_wrong_listing_prices_fail(self):
        for defect in ('expired', 'identity', 'unverified'):
            payload = self.payload()
            evidence = payload['recommendations'][0]['provenance']['price_evidence']
            if defect == 'expired':
                evidence.update(evidence_method='recent_verified_cache', cached_evidence={
                    'verified_at': (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()})
            elif defect == 'identity':
                evidence['source_url'] = 'https://www.amazon.in/dp/B0GNZPHXGN'
            else:
                evidence['verified'] = False
            self.assertEqual(self.check(payload)['status'], 'FAIL')

    def test_unchanged_evidence_requires_same_count_order_and_fit(self):
        first = self.payload()
        second = copy.deepcopy(first)
        self.assertEqual(check_repeat(first, second)['errors'], [])
        second['recommendations'] = []
        self.assertTrue(check_repeat(first, second)['errors'])
        second['fit_diagnostics'][0]['features'].append('new observed evidence')
        self.assertFalse(check_repeat(first, second)['evidence_unchanged'])

    def test_available_three_and_partial_status_contract(self):
        payload = self.payload()
        payload['stage_counts'] = {'qualifying_unique_models': 3}
        self.assertTrue(any('Three eligible' in e for e in self.check(payload)['errors']))
        payload.pop('stage_counts')
        payload['status'] = 'PASS'
        self.assertTrue(any('sufficiency' in e for e in self.check(payload)['errors']))


if __name__ == '__main__':
    unittest.main()
