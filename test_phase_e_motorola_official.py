"""Motorola manufacturer support is allowed; similarly named hosts are not."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from official_source_resolver import BRAND_DOMAINS, hostname_matches


class MotorolaOfficialTests(unittest.TestCase):
    def test_manufacturer_and_support_hosts(self):
        domains = BRAND_DOMAINS['motorola']
        for url in ('https://www.motorola.in/smartphones-moto-g-96-5g/p',
                    'https://en-in.support.motorola.com/app/answers/detail/a_id/187674'):
            self.assertTrue(hostname_matches(url, domains))
        for url in ('https://motorola.com.example.org/specs',
                    'https://fake-motorola.in/specs', 'https://amazon.in/dp/B0FHGGW5PJ'):
            self.assertFalse(hostname_matches(url, domains))
