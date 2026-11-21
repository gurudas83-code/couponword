# Coupon World — A-to-Z Completion and Release Gates
**Audit baseline:** 21 November 2026. This is a working plan, not a live-price or Google-indexing guarantee.

## Actual numbers from generated GitHub CI artifact
- Core phones: 232 unique model identities.
- Source-linked specifications: 226 models with at least one linked field.
- Official verified and sufficiently sourced: 32 models.
- Additional manufacturer / identity review remaining: 200.
- Explicit maker-verified India RAM/storage variants missing: 223.
- Exact-match, rights-checked photos: 58. Missing exact photos: 174.
- Historical dated positive price evidence: 134. Missing price evidence: 98.
- Saved third-party observations: 128 smartphone model IDs, 31 other-category IDs.
- Observed phone retailer rows: 830; fresh within six hours as of audit: 0.
- Authorized live checkout offers certified by this audit: 0.
- Earlier incomplete query audit: 451 price, 72 hard variant/features, 100 source gaps = 623.
These sets overlap. Do not add them as though they were disjoint defects.

## Product contract
Show distinct VERIFIED_IN_BAND, RESEARCH_UNPRICED, NO_CONFIRMED_MATCH, and
OUT_OF_STOCK states. A saved price is only a historical reference. Manufacturer
specs are not a dated exact SKU offer. Colour and RAM/storage must not be
silently substituted. A performance winner needs independent performance
measurements; a source-count ranking is only a research-confidence ordering.

## Stage 1 — Product identity and 232-model hygiene (P0)
Review Indian release / discontinuation, brand spelling, same hardware sold in
multiple colours, exact manufacturer model/part no., and whether a label is an
unconfirmed research identity. Maintain a reviewable evidence ledger.
Never display research-only or unreleased products as available to purchase.
Keep existing product pages and images unless a verified replacement passes QA.

## Stage 2 — Licensed images and maker-backed exact variants (P0)
For every phone, obtain original maker evidence for physical RAM, storage,
country-specific model code, chipset, 5G, camera, battery and update support.
Complete 174 photo reviews via permitted licensed files with required
attribution and exact model match. Do not scrape copyrighted retailer images.

## Stage 3 — Authorized retailer APIs and current price (P0)
Reuse the existing QuickCommerce adapter, Amazon/Flipkart/Croma retailer links,
maker-store observations and price-evidence compiler; do not start a new engine.
QuickCommerce is a third-party research provider, NOT Flipkart Affiliate API.
The current Render bridge has a per-process daily paid request allowance of
20 by default and a six-hour cache; distributed spending control is still
needed before scaling. It requires a private server-side QuickCommerce key.
An API key in GitHub Actions Secrets is not automatically available in Render.

First verify access to Flipkart Affiliate API, then Amazon India Creators API
(eligible Associates currently need 10 qualified sales in the trailing 30
days), then evaluate a licensed commercial shopping-data provider for gaps.
Check actual provider cost and terms before paying. Third-party shopping
search results may have wrong variants, refurb items or irrelevant sellers:
they are DISCOVERY, not automatic checkout-eligible deals.

Start with 20-30 high-demand confirmed India SKUs in the existing ₹10k–₹30k
bands. Compare provider success rates, confirmed exact IDs, listing URL,
merchant, RAM/storage, color, pincode, stock, INR final amount and observation
timestamp. Reject ambiguous offers. Only after a pilot passes, scale to top 50,
then all saleable SKUs. At four checks per day, 50 SKUs require 6,000
lookups/month per retailer; all 232 require 27,840 lookups/month per retailer
before extra colour/variant checks. Do not mistake quota for free access.
A discontinued phone can legitimately have NO CURRENT PRICE; show that state.

## Stage 4 — Top 3 and 623 query answers (P1)
Preserve ₹5k windows and fail-closed 5G, RAM/storage, excluded-brand and
model identity requirements. Never invent a third recommendation in a 2/3
band. Clear the 451 price queries with exact source captures, the 72 hard
feature/variant queries with manufacturer evidence, and the 100 source gaps
with linked specifications. Re-evaluate the 1,000-query corpus including
Hindi/Hinglish and voice-transcription text; no invented prices, performance
benchmarks or current-offer claims. Label partial answers accurately.

## Stage 5 — Real phone speed (P1)
Click-to-local-result <1 second is separate from first-page network-load time.
Measure LCP, CLS, interaction delay, catalogue transfer, image bytes, 4G/5G
and slow Android devices. The existing GitHub Chromium 8-10ms local code tests
are NOT evidence of 1s cold-load SLA for visitors. Use real-user GA4 field
performance plus controlled real-device p95 before claiming compliance.

## Stage 6 — Search, publisher quality and monetization (P1)
199 generated sitemap URLs exist, all linked in the latest build. Do not create
500 duplicate AI guides. Review existing category pages, maintain canonical,
noindex/editorial quality policy, clear ownership and affiliate disclosure.
Connect authorized Google Search Console and GA4 data to diagnose clicks,
impressions, indexing, outreach and outbound retailer leads. An outbound
click is NOT a proven sale or commission.

## Release checks and payment decisions
- All four existing GitHub CI gates plus the readiness test must pass.
- No secret is written to a code file, shared report, or browser bundle.
- No unauthorized live offer, counterfeit coupon, unlicensed image, or
  manufacturer fact without a checked link enters production.
- Deploy only reviewed change sets; then verify actual GitHub Pages content.
- Pricing subscriptions require provider choice, licensing and budget approval.
- Rebuild the automated 232-model readiness report after every ingestion;
  never substitute metrics from its historical sources for live sales data.

The current report is in the GitHub Actions artifact named
coupon-world-mobile-a-to-z-readiness-<run_id>. Its queues list all 232 phones
with missing fields and the distinct API observations for verified follow-up.
