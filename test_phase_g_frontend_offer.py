import subprocess
import unittest
from pathlib import Path


class FrontendOfferTests(unittest.TestCase):
    def test_display_price_url_variant_and_time_share_one_source(self):
        script = r'''
const fs = require('fs'), assert = require('assert');
const source = fs.readFileSync('app.js', 'utf8');
const start = source.indexOf('      const offers = Array.isArray(p.retailer_offers)');
const end = source.indexOf('      const why = Array.isArray(p.why_it_fits)', start);
assert(start >= 0 && end > start);
const render = new Function('p', 'escapeHTML', 'safeLink', source.slice(start,end) +
  '\nreturn {selectedPrice,productLink,variant,lastChecked,retailerHeading};');
const core = {price:7999, market_source:'https://amazon.in/dp/EXACT',
 identity_evidence:{variant:{ram_gb:'4',storage_gb:'64'}},
 provenance:{price_evidence:{source_url:'https://amazon.in/dp/EXACT',verified_at:'original-time'}},
 retailer_offers:[{price:null,product_url:'https://other.example/different',last_checked:'new-time'}]};
const result = render(core,String,String);
assert.strictEqual(result.selectedPrice,7999);
assert.strictEqual(result.productLink,'https://amazon.in/dp/EXACT');
assert.strictEqual(result.lastChecked,'original-time');
assert.strictEqual(result.variant,'4GB/64GB');
assert.strictEqual(result.retailerHeading,'Retailer');
const offer={price:7899,product_url:'https://retailer.example/exact',variant:'4GB/64GB',last_checked:'offer-time',retailer:'example'};
const alternate=render({...core,retailer_offers:[offer]},String,String);
assert.strictEqual(alternate.selectedPrice,7899);
assert.strictEqual(alternate.productLink,offer.product_url);
assert.strictEqual(alternate.lastChecked,offer.last_checked);
'''
        result = subprocess.run(["node", "-e", script], cwd=Path(__file__).resolve().parent,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
