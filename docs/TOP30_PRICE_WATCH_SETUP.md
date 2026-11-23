# India Top-30 price watch

The scheduled workflow `.github/workflows/affiliate-price-refresh.yml` runs
once a day at 17:00 IST (11:30 UTC). It has a manual `workflow_dispatch`
button for a deliberate one-time refresh. It has no `push` trigger, so code
changes do not accidentally spend paid API credits.

## Required repository secret

Configure this GitHub Actions secret:

- `QUICKCOMMERCE_API_KEY`: the private QuickCommerce API key.

The key is injected only into the workflow process and is never written to the
repository, the offer store or the public Pages artifact. The workflow fails
before making a paid request when the secret is missing.

Each run makes one bounded Flipkart search for each of the 30 approved model
keys. It does not retry a failed request, choose the cheapest sibling, or mix
RAM/storage/colour variants. The first provider-ranked in-stock exact SKU is
selected; if every exact SKU is out of stock, the first exact out-of-stock SKU
is retained with no payable price.

## Published offer contract

The refresh engine writes `data/retailer_offers.json` only after all 30 model
keys pass. A row contains the customer-useful fields below:

```json
{
  "model_key": "samsung|galaxy a56 5g",
  "verification_status": "VERIFIED",
  "source_type": "quickcommerce_authorized_api",
  "retailer": "flipkart",
  "retailer_product_id": "exact-provider-sku",
  "brand": "Samsung",
  "model": "Galaxy A56 5G",
  "variant": "8GB/128GB · Light Violet",
  "product_url": "https://www.flipkart.com/-/p/-?pid=exact-provider-sku",
  "affiliate_url": "https://www.flipkart.com/-/p/-?pid=exact-provider-sku",
  "availability": "in_stock",
  "price": 33175,
  "mrp": 49999,
  "currency": "INR",
  "checked_at": "2026-11-23T11:30:00+00:00",
  "last_checked": "2026-11-23T11:30:00+00:00"
}
```

The provider deeplink is a verified retailer buying destination. The
compatibility `affiliate_url` field keeps the existing engine contract, but
the metadata explicitly says `affiliate_attribution: not_asserted`; a
QuickCommerce key alone is not proof of Flipkart commission eligibility.

The public build copies only the safe fields into the existing price/stock
panel and the Top-30 research cards. Visitors see the exact variant, current
listed price, stock state, retailer link and checked time. Prices are not
checkout confirmation; seller, delivery, warranty, pincode and payable amount
must still be confirmed on Flipkart.

## Fail-closed rules

The batch is rejected and the previous store remains untouched when any model
has no strict model/brand/SKU match, an invalid product URL, an ambiguous
physical variant, an invalid price, an unknown stock state, a stale timestamp,
or a non-INR response. All 30 approved model keys must be present before the
store is replaced.

The older `quickcommerce_third_party_research` adapter remains private
research-only. It is not silently promoted by this workflow. Only rows emitted
by `scripts/refresh_quickcommerce_affiliate_offers.py` use the authorized
publication source type.

