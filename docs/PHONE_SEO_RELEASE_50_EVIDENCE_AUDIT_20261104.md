# Phone SEO Release 2 — evidence review and 50-page editorial gate
**Date:** 4 November 2026  
**Site:** https://coupon-world.in/phones/  
**Repo source:** `data/phone_seo_editorial_reviews.json`

## Editorial decision

Publish **50 distinct smartphone model-level research pages**: 20 existing curated pages plus 30 additional records for which a manufacturer-hosted model/specification source was located and the existing workbook supplies at least 9–10 individually linked facts.

This release is **not** a new phone comparison or scoring engine. It does not promote partial model research into certified RAM/storage variant identity, current retailer availability, verified purchase offers, independent real-world performance, phone photography rights or hands-on testing. It does not add irrelevant search-keyword permutations.

### Net-new publication by prior catalogue state

| Pre-review catalogue category | Additional pages | Source quality rule |
|---|---:|---|
| OFFICIAL_VERIFIED | 5 | Original catalogue status plus manufacturer product page and >=10 recorded facts |
| PARTIALLY_VERIFIED | 9 | Separate curated model-name/source review plus >=9–10 recorded manufacturer-linked facts; partial label remains |
| RESEARCH_ONLY prior to workbook application | 16 | Separately confirmed manufacturer source, >=10 recorded manufacturer-linked fields; builder labels research as partial when workbook specs exist; no exact-variant certification |
| Existing initial curated pages | 20 | Preserve prior source-evidence rule and URLs |
| **Total** | **50** | All retained in same 232-model research universe |

The 30 additions are specifically named in the JSON editorial-review file, including source URLs, check date and limitations; the builder stops if any model's identity or expected manufacturer link is unavailable.

## Verified correction made before publication

**Samsung Galaxy F05 — network support was wrong.** Saved workbook erroneously said **5G** for Galaxy F05 (Samsung model SM-E055FDBD). The Samsung India product specification lists only **2G GSM, 3G WCDMA, 4G LTE FDD and LTE TDD**. The saved workbook now has `network_support = 4G LTE`, with source checked 4 Nov 2026. Its new public page and regression tests must show the corrected value.

Manufacturer source: https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f05-blue-64gb-sm-e055fdbdins/

## Explicitly excluded from distinct SEO routes

1. `samsung|galaxy a06 5g light` — "Light Gray" appears in the original product colour/variant name, not a separately certified Galaxy A06 5G model. Use **Samsung Galaxy A06 5G** as the canonical editorial model instead.
2. `samsung|galaxy s24 5g` — same Samsung Galaxy S24 product as existing `samsung|galaxy s24`; don't produce a duplicate canonical page.
3. Unreviewed, thin or conflicting records in the remaining 232-model discovery research are not automatically indexed; search users can still see those candidates with evidence limitations.

## Source-reviewed groups

The new batch includes model-level sources from:

- **Apple**: iPhone 16, iPhone 16 Pro, iPhone 17, iPhone 17 Pro and iPhone 17 Pro Max, from Apple India specification/support pages
- **Google**: Pixel 9a, Pixel 10 and Pixel 10a, from Google India specification pages
- **Samsung**: Galaxy F05, A06 5G, A27 5G, A35 5G, A55 5G, A57 5G, Galaxy F70 Pro 5G and M47 5G from Samsung India
- **Redmi/Xiaomi**: Redmi 13 5G, Redmi Note 13 5G, Note 13 Pro 5G, A3x and Xiaomi 14 Ultra
- **OnePlus**: 12, Nord 4, N6 Lite
- **Motorola**: Edge 60 Fusion
- **Others**: iQOO 13, POCO X7 Pro, OPPO Find X9, vivo X200 Pro and realme P4 Lite 5G

Brand model/source matches were checked on relevant official manufacturer pages/search results. This is **not** a manual field-by-field independent testing program. Existing workbook facts may still require future audit and correction; buyers should follow the source under every field.

## Release and audit invariants

- Exactly **50** distinct authored model URLs + one hub; build fails if a reviewed source/model/status/coverage gate fails.
- Research catalogue stays at **232 model cards / 235 discovery records / 10 frozen canonical variants** unless independently upgraded and re-tested.
- Canonical URL and breadcrumb/CollectionPage schema, HTML link discoverability, source link per displayed fact and honest missing-field sections.
- **Zero** current merchant prices/stock, fake product offers, aggregate ratings, anonymous auto-generated testimonials or independently tested "Top 3" claims.
- Existing price rule: **0% price weight in performance rankings**, dated reference only for budget filtering.
- GitHub PR must pass existing technical, ranking and specification tests plus new exact-count, F05 correction, duplicate suppression, manufacturer URL and real Chromium QA at 390/768/1440 px.
- GitHub Pages production deploy must confirm live hub, Galaxy A56, Google Pixel 10, Galaxy F05 corrected network, under-₹15k guide and sitemap.

## Beyond the first 50

The backlog still includes many raw research models with source URLs but not enough editorial identity/field confidence. Do not publish them in bulk. Prioritize **real buyer questions** from Google Search Console, then deepen genuine evidence and comparisons. Expand to 75–100 pages only after source audit and observed demand support distinct intent.

Google indexing, rankings, traffic, affiliate earnings and current retail offer eligibility **are not determined by GitHub tests**. Verify these in Search Console/GA4 and the existing merchant-validation pipeline.
