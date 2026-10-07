import sys,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from promote_mobile_canonical import fetch_amazon_identity
class ExactListingCapacityTests(unittest.TestCase):
    def fetch(self,ram='4 GB',storage='64 GB',title='realme C83 5G Smartphone 4+64GB Green',section='productOverview_feature_div',asin='B0GPWRYNM1'):
        html=f'<title>{title}</title><span id="productTitle">{title}</span><input id="ASIN" value="{asin}"><div id="{section}"><table><tr><td>RAM Memory Installed Size</td><td>{ram}</td></tr><tr><td>Memory Storage Capacity</td><td>{storage}</td></tr></table></div>'
        response=SimpleNamespace(status_code=200,url='https://www.amazon.in/dp/B0GPWRYNM1',text=html)
        with patch('promote_mobile_canonical.requests.get',return_value=response):
            return fetch_amazon_identity('B0GPWRYNM1','realme C83 5G 4GB RAM 64GB Storage','realme')
    def test_exact_product_table_can_supply_missing_physical_ram(self):
        result=self.fetch();self.assertEqual(result['strict_status'],'AUTO_REUSE');self.assertEqual(result['exact_listing_capacity'],{'ram_gb':'4','storage_gb':'64'});self.assertEqual(result['page_title'],'realme C83 5G Smartphone 4+64GB Green')
    def test_wrong_variant_ambiguous_or_unbound_table_never_rescues(self):
        for kwargs in ({'ram':'8 GB'},{'ram':'4 GB + 4 GB virtual'},{'storage':'128 GB'},{'title':'realme C71 5G 4+64GB Green'},{'section':'related_products'},{'asin':'B0WRONG123'}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(SystemExit):self.fetch(**kwargs)
if __name__=='__main__':unittest.main()
