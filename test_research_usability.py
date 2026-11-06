"""Regressions for public budget semantics and source-preserving presentation."""
import json
import unittest
from pathlib import Path
from python.phone_research_pages import specification_label, specification_value
from python.phone_guides import budget_examples

ROOT = Path(__file__).resolve().parent

class UsabilityTests(unittest.TestCase):
    def test_clock_is_not_chipset_and_units_are_explicit(self):
        item = {'value': '2.75 GHz, 2 GHz', 'label': 'Chipset'}
        self.assertIn('CPU clock', specification_label('chipset', item))
        self.assertIn('CPU क्लॉक', specification_label('chipset', item, hindi=True))
        self.assertEqual(item['label'], 'Chipset')  # source record stays intact
        for key, value, expected in [('display_inches', 6.7, '6.7 in'),
                                     ('display_refresh_max_hz', 120, '120 Hz'),
                                     ('battery_mah_typical', 5000, '5000 mAh')]:
            self.assertEqual(specification_value(key, {'value': value}), expected)
        self.assertEqual(specification_value('battery_mah_typical', {'value': '5000 mAh'}), '5000 mAh')

    def test_budget_examples_match_actual_dated_gate_and_both_languages(self):
        catalogue = json.loads((ROOT/'public/data/mobile_research_catalogue.json').read_text())
        cards = catalogue['model_cards']
        for cap in (10000, 15000, 20000, 30000, 50000):
            guide = {'slug': f'phones-under-{cap}'}
            english = budget_examples(ROOT/'public', guide)
            hindi = budget_examples(ROOT/'public', guide, hindi=True)
            self.assertEqual(english.count('<li>'), hindi.count('<li>'))
            self.assertLessEqual(english.count('<li>'), 6)
            for card in cards:
                from python.phone_research_pages import slug_for
                if f'/phones/{slug_for(card)}/' in english:
                    ref = card['research_budget_reference']
                    self.assertLess(ref['reference_price_inr'], cap)
                    self.assertIn(str(ref['checked_at']), english)
            if english:
                self.assertIn('not a performance ranking', english)
                self.assertNotIn('₹', english)  # amounts stay hidden
        self.assertEqual(budget_examples(ROOT/'public', {'slug': 'phone-camera-guide'}), '')

if __name__ == '__main__': unittest.main()
