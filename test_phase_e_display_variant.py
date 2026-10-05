"""Display marketing must not introduce a sibling identity."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from resolver_engine import parse_identity
from mobile_exact_identity_gate import AUTO_REUSE, classify_mobile_identity_reuse

class DisplayVariantTests(unittest.TestCase):
    base='Samsung Galaxy A06 5G 4GB RAM 64GB Storage'
    def test_hd_plus_display_is_not_a_model_variant(self):
        for suffix in ('HD Plus Display','HD Plus 90Hz Display'):
            self.assertNotIn('plus',parse_identity(self.base+' '+suffix).variant_tokens)
            self.assertEqual(classify_mobile_identity_reuse(self.base,self.base+' '+suffix,expected_brand='Samsung')['status'],AUTO_REUSE)
    def test_actual_plus_sibling_is_retained(self):
        title=self.base.replace('A06','A06 Plus')+' HD Plus 90Hz Display'
        self.assertIn('plus',parse_identity(title).variant_tokens)
        self.assertNotEqual(classify_mobile_identity_reuse(self.base,title,expected_brand='Samsung')['status'],AUTO_REUSE)
    def test_capacity_and_network_conflicts_stay_blocked(self):
        for title in (self.base.replace('4GB','8GB'),self.base.replace('64GB','128GB'),self.base.replace('5G','4G')):
            self.assertNotEqual(classify_mobile_identity_reuse(self.base,title+' HD Plus 90Hz Display',expected_brand='Samsung')['status'],AUTO_REUSE)
    def test_unqualified_plus_is_not_suppressed(self):
        for title in ('Samsung Galaxy A06 Plus','Samsung Galaxy A06 HD Plus'):
            self.assertIn('plus',parse_identity(title).variant_tokens)

if __name__=='__main__':unittest.main()
