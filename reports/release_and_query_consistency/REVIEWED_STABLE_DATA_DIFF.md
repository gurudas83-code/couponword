# Reviewed stable-data diff

Base source: b3b6539cf7661766a43934ca3ff00ea74c7b1eb4

The dirty worktree was not staged or modified. The release candidate copies only
the following verified fields into tracked release inputs.

| File | Base SHA-256 | Candidate SHA-256 | Change |
|---|---|---|---|
| data/phase_e_release_evidence.json | c6b323849b0886e3eda15a6420dfa9499ab288aa75fd6954335c153a890984bf | a389896101e4c5d768d30255e98bf34eb109bc1b6c4048fed90021c667a167bc | Add one official exact-variant record |
| data/retailer_product_registry.json | 18be435307953f79028a87dcfa463b498c2eb5fa8ddc799217a484db2d56d8e0 | 2afd358394e0e58be02184bb295000aff6adbfb39a15a2c83b31db5a708c234b | Add Vivo manufacturer mapping |
| data/retailer_offers.json | 205b2411d51a9f78818b7e78c366ba8b0d2f019cef5192fd7cb9534643d48f78 | dc8f730c830bfc6cbf75d521b603fc81108360727ee1e8814187cd0147c0bfbf | No T5 Pro offer added; expired observation excluded |

Added evidence:

- ASIN: B0H6F4KZGF
- Canonical product: cw-mobile-96
- Exact physical variant: 8 GB RAM / 128 GB storage
- Official URL: https://shop.vivo.com/in/product/10344?skuId=19410
- Manufacturer SKU: 19410
- Resolver: verified; fetch: success; page identity: 1.0
- Observation: 2026-10-14T17:45:11Z

The Amazon ASIN and Vivo manufacturer SKU remain separate registry identifiers.
The dirty Vivo offer (INR 41,999, in stock, observed 2026-10-14) is outside the
six-hour freshness window at review time and is deliberately absent from the
candidate release offer store. It must be refreshed before this product can be
budget-eligible.
