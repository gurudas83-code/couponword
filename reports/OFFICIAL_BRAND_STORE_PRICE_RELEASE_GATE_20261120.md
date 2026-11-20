# Official India brand-store price integration — evidence and release gate (20 Nov 2026)

## Verified source discovery
- Samsung India has a purchase configurator for Galaxy S26/S26+/FE at https://www.samsung.com/in/smartphones/galaxy-s26/buy/ . It requires selecting device, RAM/storage, colour and often location before a payable price can be attributed to an exact SKU.
- Samsung's comparison page https://www.samsung.com/in/smartphones/compare/ exposes product model codes and displayed prices, but these cannot be applied to a different model/variant.
- OPPO India has a storefront at https://www.oppo.com/in/store . Its category cards say 'From ₹...' and sometimes show crossed-out reference prices and promotions. Category 'From' prices are **not** exact-variant quotes and must not be imported into the current-price feed.
- OPPO K13 5G product information https://www.oppo.com/in/smartphones/series-k/k13-5g/ does not itself establish an exact-variant payable price.

## Existing branch
- Historical manufacturer-announced prices are explicitly non-live and ineligible for purchase/budget matching.
- The preceding 176/232 any-dated-price-record count is historical coverage, **not** live-price coverage. 56 remain without any dated record per preceding branch report.
- This audit does **not** claim a new current price, API integration, automated six-hour refresh, or deployment.

## Acceptance criteria before adding a live brand price
1. Exact catalogue key and Indian manufacturer SKU, RAM, storage, colour (when applicable).
2. Official India HTTPS product purchase URL; not a press release, search result, or product family landing page.
3. Current payable standalone price excluding conditional exchange, financing, bank discounts and trade-in; separately label any unconditional sitewide sale discount.
4. Explicit availability and pincode when location-specific, observation timestamp with timezone.
5. Source-specific allowed host, no fabricated price on failed scrape/API or CAPTCHA.
6. Expire the observation after six hours; never silently turn historical price into live.
7. Check no duplicate model keys and no ranking changes; compare staging and production; deploy only after tests.

## Release status
**BLOCKED:** exact current brand-store SKU quotes for the 56 missing catalogue keys have not been confirmed. Do not merge/deploy as if verified.
