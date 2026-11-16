# QuickCommerce → Flipkart research integration (feature branch only)

**Safety:** This is an *opt-in*, read-only adapter. It does not alter the
default \`RetailerConnectorManager\`, checkout links, public pages, offers DB,
canonical URLs, SEO pages, sitemap, production deployment, or ranking.

## What is implemented

- Uses the existing \`RetailerOffer\` contract and \`normalize_offer\`.
- Accepts QuickCommerce's documented \`GET https://api.quickcommerceapi.com/v1/search\`
  response and \`X-API-Key\` authentication.
- Matches exact manufacturer, model, RAM, storage, optional color,
  Flipkart PID and HTTPS deeplink.
- Stores price/MRP/availability as **research observations** with provider
  request ID. Does not claim that marketplace metadata is manufacturer specs.
- Rejects missing/inconsistent product identity, unknown stock flags,
  nonpositive prices for available products, and non-INR data.
- Does not save anything to \`data/retailer_offers.json\`, does not publish
  any API price and does not auto-call the provider.
- Existing \`retailer_publication_gate.py\` continues to reject this third-party
  source, even if a record is independently reviewed.

## Dry-run a known saved response (zero API credits)

From the repo root:

\`\`\`bash
python -m unittest -v test_quickcommerce_flipkart_adapter
\`\`\`

To inspect the outcome interactively:

\`\`\`bash
PYTHONPATH=python python - <<'PY'
from canonical_product import CanonicalProduct
from quickcommerce_flipkart_adapter import dry_run
p=CanonicalProduct(
    product_id="cw-api-dryrun-a56",title="Samsung Galaxy A56 5G",
    brand="Samsung",model="Galaxy A56 5G",variant="8GB/128GB",
    category="Mobiles",identifiers={},
    attributes={"color":"Light Violet"},source_product_id="fixture",
    confidence=0.9)
print(dry_run("tests/fixtures/quickcommerce_flipkart_a56_search.json",p))
PY
\`\`\`

Expected: product ID \`MOBHQBDXXJUDBFVH\`, research price
\`33175.0\`, \`publishable: False\`.

## Optional real API smoke test (costs 1 API credit)

Never commit or paste an API key. Configure a private
\`QUICKCOMMERCE_API_KEY\` environment secret, then explicitly instantiate
\`QuickCommerceFlipkartConnector()\` and call \`get_offer(product)\` using the
same product above. The default application remains unchanged.

The 15-second network timeout is explicit. The key is sent only in an
\`X-API-Key\` header, never in a query string. Rate limits and request errors
propagate as failures; no invalid offer is substituted.

## Remaining work before production

1. Confirm QuickCommerce and Flipkart data licensing/public affiliate price
   display rights *in writing*. This third-party source is **not** the
   official Flipkart affiliate feed.
2. Validate actual real-time lookup with a private key in an isolated CI
   environment. Confirm variants and prices on product pages.
3. Add authorized provider configuration, durable scheduler and storage only
   after explicit agreement on rights, refresh budget and rollout policy.
4. Keep all 232 research models and existing evidence/SEO gates intact;
   start the active refresh pool with 30 validated models.
5. No use of price or affiliate status as a capability ranking signal.
