# India Top-30 price watch

The scheduled workflow `.github/workflows/affiliate-price-refresh.yml` runs at
17:00 IST (11:30 UTC) every day. It also runs when the workflow or its refresh
engine changes, so a configuration change can be tested immediately.

## Required repository secrets

Configure these two GitHub Actions secrets before expecting a public refresh:

- `AFFILIATE_PRICE_FEED_URL`: HTTPS endpoint for the authorized paid affiliate
  feed.
- `AFFILIATE_PRICE_FEED_TOKEN`: bearer token for that endpoint.

The values are never stored in the repository or printed by the workflow. The
workflow fails clearly when either secret is absent instead of reporting a
successful no-op.

## Feed contract

The endpoint must return either an object with an `offers` array or the array
itself. Every row must include the fields required by
`python/retailer_publication_gate.py`, plus a Top-30 identity:

```json
{
  "model_key": "samsung|galaxy a56 5g",
  "verification_status": "VERIFIED",
  "source_type": "amazon_pa_api",
  "retailer_product_id": "exact-sku",
  "product_url": "https://retailer.example/product/exact-sku",
  "affiliate_url": "https://retailer.example/product/exact-sku?affiliate=tag",
  "availability": "in_stock",
  "price": 29999,
  "checked_at": "2026-11-23T11:30:00+00:00"
}
```

The engine rejects stale rows, unknown availability, non-approved models,
missing exact product identity, missing buying destinations for in-stock rows,
and incomplete feeds. All 30 approved model keys must be represented before
the old store is replaced. A failed refresh leaves the last store untouched.

The existing `QUICKCOMMERCE_API_KEY` is a separate research-only provider and
is intentionally not promoted to public affiliate prices without an authorized
affiliate feed contract.

