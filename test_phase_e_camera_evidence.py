import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from product_fit_signal_builder import camera_signal, smartphone_battery_signal

class CameraEvidenceTests(unittest.TestCase):
    def test_official_thousands_separator_does_not_create_zero_capacity(self):
        result = smartphone_battery_signal('5,000 mAh battery; Battery Capacity (mAh, Typical) 5000')
        self.assertEqual(result['measurements']['capacity_mah'], [5000.0])
        self.assertEqual(result['basis'], 'capacity_proxy')
        self.assertEqual(result['match'], 0.4167)
        self.assertEqual(smartphone_battery_signal('Battery Capacity (mAh, Typical) 5,000')['match'], 0.4167)

    def test_official_a06_negative_and_duplicate_labels(self):
        text = '50MP Dual Camera; Rear Camera - OIS No; Front Camera - OIS No; Rear Camera - OIS; no noise only voice'
        self.assertEqual(camera_signal(text)['match'], 0.2)
        self.assertNotIn('stabilization', camera_signal(text)['reason'])

    def test_noise_and_bare_labels_are_not_evidence(self):
        for text in ['noise cancellation', 'Rear Camera - OIS', 'No OIS', 'without optical image stabilization', 'OIS: not supported']:
            with self.subTest(text=text):
                self.assertIsNone(camera_signal(text)['match'])

    def test_positive_rear_evidence_survives_front_negative(self):
        for text in ['Rear Camera - OIS Yes; Front Camera - OIS No', '50MP OIS camera', 'camera with optical image stabilization']:
            with self.subTest(text=text):
                self.assertEqual(camera_signal(text)['match'], 0.7)

if __name__ == '__main__':
    unittest.main()
