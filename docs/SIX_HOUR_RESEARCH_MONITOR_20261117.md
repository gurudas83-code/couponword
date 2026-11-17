# Six-hour Coupon World research monitoring agent

## Reused engines
- python/quickcommerce_flipkart_adapter.py: one authenticated third-party QuickCommerce Flipkart search.
- scripts/quickcommerce_catalogue_audit.py: strict model/brand/PID, stock and price observations, reference-only images and no automatic publication.
- python/retailer_publication_gate.py: existing authorized-source and fresh-offer publication policy, unchanged.
- .github/workflows/mobile-integrity-6h.yml: separate six-hour links, research integrity and answer QA, not automatic specification updates.
- .github/workflows/amazon-catalog-sync.yml: separate Amazon and Flipkart source readiness and offer gate, does not create verified prices.
- python/official_source_resolver.py, python/official_spec_extractor.py: manufacturer research for manual review, deliberately not crawled automatically every six hours.
- python/retailer_connector_manager.py, python/multi_retailer_orchestrator.py, product identity and recommendation engines: unchanged.

## New schedule
- .github/workflows/six-hour-research-monitor.yml: UTC 02:23, 08:23, 14:23, 20:23; GitHub scheduler can run late.
- Scheduled calls: at most 4 paid searches per six-hour slot and 16 scheduled searches per UTC day, subject to a valid key and provider availability.
- Rotating mix: 3 mobile models plus 1 TV/earbud with an explicit model code. No invalid-code TV/earbud queries. Manual and pull-request runs are zero-call offline by default.
- The selected observations include matching model candidates, location-specific price/stock, matching Flipkart IDs and image references. These are NOT verified exact variants, licensed photos or approved public offers.
- Evidence saved only as ephemeral Actions artifact under private_observations, retained 7 days. GitHub artifact accessibility follows repository visibility; it is not a secure long-term price-history database.
- This agent reads the catalogue and existing authorized-source offer gate. It never modifies ranking, public catalogue, images, SEO, affiliate links or stored offers. The old six-hour source and link monitors continue independently.
- Key missing: offline report, zero paid calls. API error: stop immediately, no retries. Existing connector 15-second request timeout and 1-second rate limit remain.
- Manual live calls are capped at 4 each; manual calls can increase total daily usage beyond the scheduled 16.

## Scope / limitations
- 232 mobiles + 20 TVs + 20 earbuds exist in the research inventory. The small credit cap means NOT every product is refreshed every six hours. Querying all 232 mobiles 4 times daily would need 928 mobile searches/day before TVs or earbuds.
- Amazon/Croma live prices require their own authorized feeds. The QuickCommerce connector being used is Flipkart-platform only.
- Manufacturer specification data is counted and the separate integrity monitor checks links; automatic fresh-value specification approval remains intentionally disabled.
- Flipkart/API image references are not republication rights. Public images need explicit permission and exact-model visual review.
- Provider cost per request is unverified. Review credits regularly. Suspend the schedule if billing or terms do not support the searches.

## Offline tests
Run: python -m unittest -v test_quickcommerce_flipkart_adapter test_quickcommerce_catalogue_audit test_six_hour_research_monitor

Offline dry-run: python scripts/six_hour_research_monitor.py
Optional manual live: python scripts/six_hour_research_monitor.py --live --max-calls 1, using an environment secret, not a CLI key.
