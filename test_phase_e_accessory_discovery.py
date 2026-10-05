"""Reject accessory cards observed in frozen Gate 3 Samsung discovery."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from market_discovery import category_accessory_gate

class AccessoryDiscoveryTests(unittest.TestCase):
    def test_observed_accessories_are_rejected(self):
        for title in (
            'samsung Adapto 12 2.4A 12W Fast Wall Charger for iPhone',
            'samsung 25W Charger for Samsung',
            'samsung 65W Car Charger Fast Charging Dual Port Type C',
            'Samsung Mobile Phone Skins Compatible',
            'Phone Case in Box for Lava Bold N2 4GB RAM 64GB Storage',
            'samsung Original-Galaxy Wired In Ear Earphones For All Samsung Smartphones',
        ):
            with self.subTest(title=title):
                self.assertEqual(category_accessory_gate(title,'smartphone')['status'],'reject')

    def test_phone_bundles_and_without_charger_stay_eligible_for_discovery(self):
        for title in (
            'Samsung Galaxy A06 5G 4GB RAM 64GB Storage Without Charger',
            'Lava Bold N2 4GB RAM 64GB Storage 10W Charging Charger & Phone-Case in Box',
            'Lava Bold N2 Lite 3GB RAM 64GB Storage Charger & Phone-Cover in Box',
            'Lava Virat V1 Smartphone 64GB 4GB RAM Himalayan Silver',
            'Samsung Galaxy F70e 5G 6GB RAM 128GB Storage',
        ):
            with self.subTest(title=title):
                self.assertEqual(category_accessory_gate(title,'smartphone')['status'],'pass')

if __name__=='__main__':unittest.main()
