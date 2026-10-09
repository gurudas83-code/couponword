import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from product_fit_signal_builder import software_support_signal


class SupportDateKeyTests(unittest.TestCase):
    def test_stored_official_key_matches_visible_label(self):
        self.assertEqual(
            software_support_signal('security_update_period_valid_until: 31 January 2032'),
            software_support_signal('Security Update Period (Valid until): 31 January 2032'))

    def test_unrelated_expired_and_invalid_dates_do_not_grant_support(self):
        for text in ('launch_date: 31 January 2032',
                     'warranty_valid_until: 31 January 2032',
                     'security_update_period_valid_until: 31 January 2000',
                     'security_update_period_valid_until: 31 February 2032'):
            self.assertIsNone(software_support_signal(text)['match'])
