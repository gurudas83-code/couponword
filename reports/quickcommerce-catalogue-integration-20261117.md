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

## Completed live audit results

Run 44131040109 completed successfully. Observations were collected sequentially between 2026-11-17 16:54:25 and 17:07:52 UTC (22:24:25–22:37:52 IST), for the inherited smoke-test location/pincode 110001. They are not pan-India availability guarantees.

| Category | Entries searched | Entries with strict model candidates | Unresolved |
| --- | ---: | ---: | ---: |
| Mobiles | 232 | 106 | 126 |
| TVs | 20 | 0 | 20 |
| Earbuds | 20 | 0 | 20 |
| Total | 272 | 106 | 166 |

The matched mobile entries yielded 707 listing candidates: 325 observed in stock and 382 observed out of stock. These are candidate rows, not necessarily unique retailer SKUs across catalogue entries. There were 5,097 image references across the candidates, not 5,097 unique licensed photographs. All remain research-only; zero new public prices, stock claims, product images or buyable offers were published.

Evidence artifact: https://github.com/gurudas83-code/couponword/actions/runs/44131040109/artifacts/14351566007 (GitHub artifact retention ends 1 December 2026). A persistent private copy of the audit ZIP was also retained for the user.

The initial audit used commit 1873f0bdfbb1d3c68b20ed9c6eca11cbce3d716a. PR #112 subsequently fixed parenthesized model names such as Nothing Phone (3a); the completed observations were not silently relabeled or replayed as fresh. Unresolved rows can reflect retailer naming, absent model codes, no search hits or strict validation, and must not be called out of stock.

## Remaining publication prerequisites

- Resolve the 126 unmatched mobile entries and 40 unmatched TV/earbud entries with exact listing/model-code evidence.
- Review actual RAM/storage/color and region for each candidate before binding it to canonical products. Only 10 exact frozen variants currently exist in the technical preview.
- Clear image rights and exact-model visuals before adding any of the new image references to public pages. Existing 58 photo references remain unchanged; 174 mobile cards still have no photo.
- Flipkart affiliate terms (https://affiliate.flipkart.com/terms-and-conditions, section 2) make the content license conditional on acceptance and referral use, and restrict using that content to send sales elsewhere. QuickCommerce API access is not proof of that license, especially for a photo opening Amazon/Flipkart/Croma options.
- Keep QuickCommerce observations attributed to the third-party research source. The existing authorized-source publication gate is unchanged.

Integration PRs #111 and #112 are merged. The final implementation passed 23 local offline tests and all five PR CI gates; both code deployments and their published-page smoke checks succeeded. No ranking or SEO source files changed.
