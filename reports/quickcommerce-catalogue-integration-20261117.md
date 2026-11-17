# QuickCommerce catalogue integration - 17 November 2026

## Verified baseline

- Repository baseline: `2fb29c8afbb8b97f15fec0953707433770d7b61b`.
- Existing smoke: https://github.com/gurudas83-code/couponword/actions/runs/44125900899 - successful one-call research observation, not a catalogue audit.
- Smoke observation at 2026-11-17T16:27:14Z: Samsung A56 listing `MOBHQBDXXJUDBFVH`, INR 33,294, in stock. This is historical, location-specific provider evidence, not a current checkout promise.
- Existing public catalogue: 232 mobile cards. 58 have photo references and 174 have none. All 58 referenced asset paths exist in the baseline Git tree and all have author, source and license URL fields. This checks recorded provenance and asset presence; it is not a new visual or rights review.
- Existing secondary catalogue: 20 TVs and 20 earbuds (stored under the legacy `accessories` category).

## Changes

The existing connector now exposes its one-request search method for the bounded audit. The default retailer manager, public catalogues, prices, offer store, ranking formula and SEO files are untouched. Public build uses an explicit allowlist; `private_observations/` is outside it and ignored by git.

`scripts/quickcommerce_catalogue_audit.py` processes mobiles first, then TVs, then earbuds. Offline default is zero calls; live calls require an explicit cap of 0-272. Searches are sequential, at least one second apart, with a 15-second request timeout and no retries. Any request/schema error stops the batch and leaves an evidence checkpoint. Errors expose only exception class, never API keys or upstream error bodies.

Mobile title/brand, storage-specific cards, HTTPS product links and matching Flipkart PID are checked conservatively. TV/earbud candidates require an explicit model code. Each SKU retains its own observed price, availability, title, quantity and location. No cheapest-price selection or recommendation ranking occurs. Missing model codes, naming differences and no search hits stay unresolved; they do not imply the product is unavailable.

Search matches remain model candidates, not verified canonical RAM/storage/color variants. Out-of-stock listings have no payable price. Every record remains `publishable: false`. Existing strict exact-variant adapter and publication gate are preserved. Image URLs are allowlisted references only, never downloaded or published by this audit.

## Source and publication boundary

- Provider documentation: https://quickcommerceapi.com/docs - third-party search/item data, location parameters, image references, per-platform credits.
- Provider terms reviewed: https://quickcommerceapi.com/terms (last updated 26 August 2026). They describe API service access and acceptable use; this review did not establish a retailer/manufacturer image republication license.
- Provider Flipkart page: https://quickcommerceapi.com/platforms/flipkart - marketplace price/stock monitoring use cases. This is not evidence of official Flipkart affiliate-feed authorization.

Public image integration still requires documented permission/license plus exact-model visual review. Public offers require an admitted source, exact variant and fresh evidence under the existing publication policy. Do not relabel QuickCommerce as `flipkart_affiliate_feed` or weaken that gate to make the audit green.

## Validation

22 local offline tests pass: original adapter tests plus catalogue ordering/counts, model/brand/currency/PID rejection, storage separation, boolean/NaN price rejection, stock handling, image URL references, TV model-code boundaries, call caps, zero-call default and redacted stop-on-error behavior.

GitHub CI on `1873f0bdfbb1d3c68b20ed9c6eca11cbce3d716a` passed adapter tests, static SEO, research quality, mobile integrity and Chromium mobile/tablet/desktop journeys. Live bounded audit: https://github.com/gurudas83-code/couponword/actions/runs/44131040109 (results are separate from fixture tests).
