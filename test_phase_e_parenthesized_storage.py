import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from shopping_intelligence_pipeline import runtime_profile_from_extraction

class ParenthesizedStorageTests(unittest.TestCase):
    title='Samsung Galaxy F70e 5G (Spotlight Blue, 128 GB) (4 GB RAM)'
    def profile(self,title=None,verified=True,owner='cw-mobile-82',specs=None,discovery_only=False):
        title=self.title if title is None else title
        with patch('retailer_product_registry.find_canonical_product_id',return_value=owner):
            return runtime_profile_from_extraction(
                candidate={'asin':'B0GNZSK9HJ','title':title},identity={},
                resolved={'status':'retailer_identity_verified' if verified else 'unknown','official_title':'' if discovery_only else title},
                extraction={'search_name':'' if discovery_only else title,'specifications':dict(specs or {}),'review':{'status':'verified_live_retailer_identity'}},
                intent={'category':'smartphone'})
    def test_observed_title_recovers_physical_storage(self):
        self.assertEqual(self.profile()['attributes'],{'ram_gb':4,'storage_gb':128})
    def test_unverified_unowned_or_discovery_only_cannot_supply_storage(self):
        for kwargs in ({'verified':False},{'owner':''},{'discovery_only':True}):
            with self.subTest(kwargs=kwargs): self.assertNotIn('storage_gb',self.profile(**kwargs)['attributes'])
    def test_ambiguous_or_expandable_capacity_does_not_supply_storage(self):
        for title in (self.title+' (Blue, 256 GB) (4 GB RAM)',self.title+' 64GB Storage','Phone (expandable 128 GB) (4 GB RAM)'):
            with self.subTest(title=title):
                attrs=self.profile(title=title)['attributes']
                self.assertNotEqual(attrs.get('storage_gb'),128)
    def test_existing_structured_capacity_is_preserved(self):
        self.assertEqual(self.profile(specs={'storage_gb':64})['attributes']['storage_gb'],64)

if __name__=='__main__': unittest.main()
