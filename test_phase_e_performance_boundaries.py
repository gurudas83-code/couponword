import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from product_fit_signal_builder import performance_signal, display_signal


class PerformanceBoundaryTests(unittest.TestCase):
    def test_verified_165hz_gets_existing_high_refresh_credit(self):
        base = '6.8 inch amoled '
        self.assertEqual(display_signal(base+'165Hz')['match'], display_signal(base+'144Hz')['match'])
        self.assertGreater(display_signal(base+'165Hz')['match'], display_signal(base+'60Hz')['match'])
        self.assertEqual(display_signal(base+'1650Hz')['match'], display_signal(base+'60Hz')['match'])

    def test_exact_gen5_uses_flagship_tier_without_promoting_unknown_names(self):
        self.assertEqual(performance_signal('Snapdragon 8 Gen 5')['match'], 1.0)
        for text in ('Snapdragon 8 Gen 50', 'Snapdragon 8 Gen unknown', 'Snapdragon 6 Gen 5'):
            self.assertEqual(performance_signal(text)['match'], .65)

    def test_octacore_ultrafast_is_not_intel_hardware(self):
        result = performance_signal('Lava Bold N2 5G | Octacore Ultrafast Processor | 6000 mAh')
        self.assertIsNone(result['match'])
        self.assertEqual(result['status'], 'unknown')

    def test_named_intel_tier_still_scores(self):
        self.assertEqual(performance_signal('Intel Core Ultra 7 155H')['match'], 0.8)
        self.assertIsNone(performance_signal('core ultra fast phone')['match'])

    def test_existing_named_phone_chipsets_still_score(self):
        self.assertEqual(performance_signal('Snapdragon 8 Elite')['match'], 1.0)
        self.assertEqual(performance_signal('Snapdragon 778G')['match'], 0.8)
        self.assertEqual(performance_signal('Dimensity 6300')['match'], 0.65)


if __name__ == '__main__':
    unittest.main()
