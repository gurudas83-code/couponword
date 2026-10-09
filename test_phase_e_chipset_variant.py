"""Distinguish a chipset Turbo suffix from the handset's model variant."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from resolver_engine import parse_identity
from mobile_exact_identity_gate import AUTO_REUSE,classify_mobile_identity_reuse

class ChipsetVariantTests(unittest.TestCase):
    base='vivo T5x 5G 6GB RAM 128GB Storage'
    def test_named_processor_suffix_is_not_sibling(self):
        title=self.base+' Dimensity 7400-Turbo Processor'
        self.assertNotIn('turbo',parse_identity(title).variant_tokens)
        self.assertEqual(classify_mobile_identity_reuse(self.base,title,expected_brand='vivo')['status'],AUTO_REUSE)
    def test_real_handset_turbo_is_preserved(self):
        title=self.base.replace('T5x','T5x Turbo')+' Dimensity 7400-Turbo Processor'
        self.assertIn('turbo',parse_identity(title).variant_tokens)
        self.assertNotEqual(classify_mobile_identity_reuse(self.base,title,expected_brand='vivo')['status'],AUTO_REUSE)
        self.assertIn('turbo',parse_identity('Redmi Turbo 4 8GB RAM 256GB Storage').variant_tokens)
    def test_capacity_and_network_guards_are_unchanged(self):
        for title in (self.base.replace('6GB','8GB'),self.base.replace('128GB','256GB'),self.base.replace('5G','4G')):
            self.assertNotEqual(classify_mobile_identity_reuse(self.base,title+' Dimensity 7400-Turbo Processor',expected_brand='vivo')['status'],AUTO_REUSE)

    def test_observed_dimensity_7025_ultra_is_not_handset_variant(self):
        base = 'Redmi Note 14 5G 8GB RAM 256GB Storage'
        suffix = ' Global Debut MTK Dimensity 7025 Ultra'
        self.assertEqual(classify_mobile_identity_reuse(base, base+suffix, expected_brand='Redmi')['status'], AUTO_REUSE)
        for changed in (base.replace('Note 14', 'Note 14 Ultra'),
                        base.replace('8GB', '12GB'), base.replace('256GB', '128GB'),
                        base.replace('5G', '4G')):
            self.assertNotEqual(classify_mobile_identity_reuse(base, changed+suffix, expected_brand='Redmi')['status'], AUTO_REUSE)

if __name__=='__main__':unittest.main()
