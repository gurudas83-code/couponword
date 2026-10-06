"""Battery units and workloads must not silently become equivalent evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from intent_engine import parse_query
from product_fit_signal_builder import build_fit_signals, smartphone_battery_signal, category_battery_signal, battery_signal


class BatteryTests(unittest.TestCase):
    def test_standby_audio_talk_and_unlabelled_hours_do_not_score(self):
        for text in ('340Hrs Stand By', 'Stand By Time** 340Hrs',
                     'Audio Playback Time (Hours) Up to 80', 'Talk Time 50 hours',
                     '100 hours', 'charging time 2 hours'):
            with self.subTest(text=text):
                self.assertIsNone(smartphone_battery_signal(text)['match'])

    def test_standby_never_inflates_capacity(self):
        capacity = smartphone_battery_signal('5000mAh')
        mixed = smartphone_battery_signal('5000mAh; Stand By Time** 340Hrs')
        self.assertEqual(mixed['match'], capacity['match'])
        self.assertEqual(mixed['measurements']['standby_hours'], [340])
        self.assertEqual(mixed['basis'], 'capacity_proxy')
        self.assertEqual(mixed['status'], 'derived')

    def test_minutes_and_label_first_hours_are_normalized(self):
        for text in ('Youtube Playback Time** 615min', '10.25 hours youtube playback'):
            self.assertEqual(smartphone_battery_signal(text)['measurements']['youtube_playback_hours'], [10.25])
        result = smartphone_battery_signal('Video Playback Time (Hours) Up to 17')
        self.assertEqual(result['measurements']['video_playback_hours'], [17])

    def test_capacity_cannot_mask_shorter_active_endurance(self):
        short = smartphone_battery_signal('Video Playback Time (Hours) Up to 10; 9000mAh; 340 hours standby')
        longer = smartphone_battery_signal('Video Playback Time (Hours) Up to 20; 5000mAh')
        self.assertLess(short['match'], longer['match'])
        self.assertEqual(short['basis'], 'video_playback_hours')

    def test_capacity_proxy_distinguishes_larger_batteries_without_claiming_endurance(self):
        scores = [smartphone_battery_signal(f'{n}mAh')['match'] for n in (5000, 6000, 7000, 8000)]
        self.assertEqual(scores, sorted(set(scores)))
        self.assertLess(max(scores), 1)
        self.assertIsNone(smartphone_battery_signal('20000mAh')['match'])

    def test_no_cross_field_number_capture(self):
        result = smartphone_battery_signal('Video Playback Time unknown Stand By Time 340 hours 5000mAh')
        self.assertEqual(result['basis'], 'capacity_proxy')
        self.assertNotIn('video_playback_hours', result['measurements'])

    def test_adjacent_duration_fields_do_not_leak_backward(self):
        result = smartphone_battery_signal('Talk Time 30hrs Stand By Time 340hrs Youtube Playback Time 615min')
        self.assertEqual(result['measurements']['youtube_playback_hours'], [10.25])
        self.assertEqual(result['measurements']['standby_hours'], [340])
        self.assertEqual(result['measurements']['talk_hours'], [30])

    def test_structured_attribute_order_does_not_change_measurements(self):
        attrs = {'talk_time': '30hrs', 'stand_by_time': '340hrs', 'youtube_playback_time': '615min'}
        intent = parse_query('best battery under 20000')
        left = build_fit_signals({'attributes': attrs}, intent)['battery']
        right = build_fit_signals({'attributes': dict(reversed(list(attrs.items())))}, intent)['battery']
        self.assertEqual(left, right)
        self.assertEqual(left['measurements']['youtube_playback_hours'], [10.25])

    def test_structured_profile_and_all_three_budget_intents(self):
        profile = {'attributes': {'video_playback_time_hours': {'value': 'Up to 17'},
                                 'battery_capacity_mah_typical': {'value': '5000'},
                                 'stand_by_time': {'value': '340Hrs'}}}
        for budget in ('₹20k', '₹30k', '₹50k'):
            intent = parse_query(f'best battery under {budget}')
            self.assertEqual(intent['category'], 'smartphone')
            result = build_fit_signals(profile, intent)['battery']
            self.assertEqual(result['basis'], 'video_playback_hours')
            self.assertEqual(result['measurements']['capacity_mah'], [5000])

    def test_remaining_charge_cards_do_not_become_full_discharge_endurance(self):
        observed = ('10 hours Video 11 hours Chat 70 hours Music 34 hours Call '
                    '393 hours Standby 12 hours Game 50% Charge left, even after: 7000mAh')
        for text in (observed, 'Video Playback 10 hours; 50% charge remaining; 7000mAh'):
            result = smartphone_battery_signal(text)
            self.assertEqual(result['basis'], 'capacity_proxy')
            self.assertEqual(result['measurements'], {'capacity_mah': [7000.0]})
            self.assertIn('excluded_duration_reason', result)
        self.assertIsNone(smartphone_battery_signal('Video playback 10 hours, 50% battery remaining')['match'])

    def test_other_categories_keep_existing_battery_engine(self):
        self.assertEqual(category_battery_signal({}, {'category': 'headphones'}, '50 hours'), battery_signal('50 hours'))


if __name__ == '__main__':
    unittest.main()
