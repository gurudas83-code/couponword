# Coupon World: evidence-first organic search and visitor growth plan
**Research date:** 4 November 2026  
**Target:** India smartphone research, specifications, exact memory variants and buying decisions  
**Constraint:** Reuse approved engines and scoring; price is a budget-eligibility reference only (0% weight in performance ranking). No new recommendation engine.

## Executive decision

Do **not** try to outspend 91mobiles, Smartprix and Gadgets 360 on a 10,000-model price database or auto-generate 500 barely differentiated "best" articles. Win narrower intent first: **exact phone specifications, manufacturer-source evidence, India memory variants, meaningful comparisons and candid limitations**. That is defensible with the current code and modest original research.

The existing product has 232 model research records, a strict public research search, a separate evidence-gated recommendation pipeline, 20 informative budget/priority guides, 86 dated budget references, and **zero current certified live retailer offers**. Public research sorting by specification coverage is **not performance ranking**. These constraints are features of the trust proposition; do not hide them.

## What current public research establishes

1. Google says its systems prioritize people-first, original content, and warns that mass-generated pages without value may violate scaled-content-abuse policy. Avoid templated keyword permutations, fabricated hands-on reviews, fake update dates and fake scores. Source: https://developers.google.com/search/docs/fundamentals/creating-helpful-content and https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
2. Standard <a href> links, canonical pages and an accurate XML sitemap make pages discoverable; search boxes alone are not a sufficient internal navigation structure. Source: https://developers.google.com/search/docs/specialty/ecommerce/help-google-understand-your-ecommerce-site-structure and https://developers.google.com/search/docs/crawling-indexing/links-crawlable
3. Product merchant listing enhancements are **not** for research pages that merely refer buyers to external retailers. Do not invent Product/Offer/AggregateRating schema, reviews, price, shipping, stock or availability. Source: https://developers.google.com/search/docs/appearance/structured-data/merchant-listing and https://developers.google.com/search/docs/appearance/structured-data/product-snippet
4. Competitors already offer comprehensive multi-filter smartphone finders (Gadgets 360) and price/battery/performance/review pages (91mobiles); copying their generic listicles is not a differentiator. Source: https://www.gadgets360.com/mobiles/phone-finder and https://www.91mobiles.com/list-of-phones/top-10-mobiles-below-20000-in-india
5. Monitor real Core Web Vitals: mobile **LCP ≤2.5s, INP <200ms, CLS <0.1**. Treat these as measurement targets, not current achieved scores. Source: https://developers.google.com/search/docs/appearance/core-web-vitals
6. Google Search Console reports search clicks, impressions, CTR, average position by query, page, country and device. Google Analytics tag currently exists on the homepage, but *no authenticated Search Console or GA4 traffic report was available for this research*, so **no actual visitor count, traffic forecast or keyword ranking is asserted**. Source: https://support.google.com/webmasters/answer/7576553/performance-report-search

## What was implemented in this release

- **Crawlable, curated model research**: `/phones/` hub and 20 manufacturer-source-linked smartphone specification pages published from the current public catalogue. Explicit editorial key allow-list; fail-closed minimum documented fields; original sources per field, missing data, source review date, exact memory and region caveats, honest external retailer searches, and related model links. No fake prices, scores, performance winners or product photographs.
- **Internal navigation**: HTML anchors from desktop/mobile menus, homepage hero, footer, phone guide hub, all 20 existing buying guides, the specification hub and related model pages. Do not rely on a site search box for crawling.
- **Search results metadata**: self-referential HTTPS canonical, unique informative titles/descriptions, BreadcrumbList and WebPage/CollectionPage JSON-LD; no merchant schema while buyability is not certified.
- **Accurate indexing scope**: generated sitemap includes the curated indexable pages, not all 232 uneven research models. The older thin `/seo/best-mobile-under-15000.html` becomes an immediate static redirect to the substantive `/seo/phones-under-15000.html` guide and is removed from the published sitemap.
- **Release regression gates**: build and test enforce unique canonical routes, internal link reachability, manufacturer links, source thresholds, minimum useful page text, redirect correctness, no fabricated offers/rating schema, and preservation of the existing frozen catalogue/approved scoring contracts.

## Priority keyword and content architecture

| Search intent | Best landing page | Customer value and guardrails |
|---|---|---|
| "Samsung Galaxy A56 5G specifications India" | /phones/samsung-galaxy-a56-5g/ | Actual source-linked fields, gaps and research checking date |
| "Galaxy A36 vs A56 5G" | Existing exact comparison search | Side-by-side documented specs; no ranking without comparable test evidence |
| "Best phone under 15000" | /seo/phones-under-15000.html | Helpful selection criteria + budget research link, explicitly not invented top 3 |
| "Mobile phone 8GB 256GB under 30000" | Existing exact-variant research UI | Strict identity and dated budget reference, no guessed stock |
| "Best battery / camera / gaming phone" | Existing specialty buying guides and verified lab context | Explain which source tests are comparable and where evidence is missing |
| "Samsung/OnePlus/Redmi phone specs" | /phones/ hub and curated model routes | Indexable same-brand navigation and original evidence |
| "software updates phone under X" | Existing software-support guide + model sources | Do not infer future support-end dates from an update promise |

**Do not claim query volume** until Search Console or a licensed keyword-demand source is connected. The archived 126 keyword-demand seeds can inform exploration, but are not a substitute for real search impressions and click data.

## Ninety-day operating playbook

### Phase 1 — correctness and index discovery (first 2 weeks)
- Verify Google Search Console domain ownership and Google Analytics 4 collection for the existing site; do not print identifiers, passwords or credentials in the repo.
- Submit `https://coupon-world.in/sitemap.xml` in Search Console; inspect the homepage, guide hub, 2 phone specs, an older product URL and the redirected under-15k URL. Record canonical selected, fetch/crawl status and indexing issues.
- Inspect page source rather than assuming JS rendering: verify each static model page has all necessary text and links in first-response HTML.
- Preserve a stable source review date; rebuilds alone must not invent recency. Monitor whether old SEO pages are indexed or canonicalized to better replacement pages.
- Audit Android mobile layout at 390px, tablet at 768px, desktop at 1440px; run real Chromium PR and Pages release gates.
- Measure CWV in field data and PageSpeed; fix actual slow/unstable elements by evidence, not scores fabricated from a localhost test.

### Phase 2 — earn qualified discovery (weeks 3–6)
- Each week, use **Search Console**, filter India + mobile, select non-branded queries with impressions, and prioritize pages with relevant queries but lower CTR and positions around 4–20.
- Improve the *top 5 opportunities*, not 100 pages: enrich genuine facts, original comparison methodology, corrected title/meta, source update, clarified missing specs and relevant links to existing research.
- Publish additional exact model pages **only after** the manufacturer-source, model identity and significant factual content gates pass. Avoid evergreen "best" claims when supported performance scores are missing.
- Create legitimately helpful content examples: RAM vs virtual RAM, exact Samsung India model codes, support policy vs support-end date, camera OIS vs megapixels, battery capacity vs independently measured endurance, charger-in-box caveats.
- Share useful evidence notes in appropriate discussions (tech communities, Reddit, Q&A) **only where the content directly answers a real question**; disclose ownership and avoid link spam. No automated posting or artificial backlinks.
- Produce short demonstrations of the *existing* search/compare tool for video/social audiences with clear source citations. Do not present stock device imagery as original photographs or paid endorsements as neutral.

### Phase 3 — grow from search quality, not page count (weeks 7–12)
- Expand category/brand landing hubs only if they have substantial original differentiating evidence and distinct search intent. Do not mass-publish duplicate filters as indexable pages.
- Run a weekly scorecard: verified source coverage, exact variant coverage, phone indexation, organic clicks/impressions, engaged search sessions, comparison completions, outbound retailer clicks and backend service uptime.
- Prioritize the **existing** backend pipeline to increase correctly rankable current-India phone variants. The user sees Top 3/category winners only when independent comparable performance evidence and eligible supply allow it.
- Verify API/affiliate/stock terms and retailer permission before activating current-price or buy CTAs. Dated prices remain budget references only.
- Keep indexation quality above page count. Prune/redirect thin or obsolete content only after checking real organic performance and canonical impacts in Search Console.

## Weekly operating dashboard (measurement specification, not fictional results)

| Metric | Source | Interpretation and action |
|---|---|---|
| Non-brand organic clicks, India | GSC Search results, query + country | Primary qualified-traffic outcome; compare 28-day windows |
| Impressions and average position | GSC by query/landing page | Select evidence topics to improve, not fabricated search volume |
| CTR for high-impression pages | GSC | Improve titles/descriptions only when page answers query |
| Indexed / submitted canonical URLs | GSC Page indexing + sitemap | Detect accidental duplicates, noindex and redirect issues |
| Mobile LCP/INP/CLS p75 | GSC Core Web Vitals / CrUX | Fix measured slow experiences and layout instability |
| Search-to-compare completion | Existing analytics events / GA4 | Whether visitors find useful answers |
| Search-to-retailer click | Existing tracked outbound events | Useful intent, but not proof of sale or affiliate earnings |
| Current certified offers / ranked variants | Existing backend ledger | Prevent public claims unsupported by current evidence |
| Backend health and response latency | Existing health and release checks | Prevent dead-end recommendations; show fallback when unavailable |

**Suggested internal planning milestones, not forecasts:** 100 → 500 → 1,000 *quality daily visits* only after measured acquisition and retention justify each stage. A calendar alone does not create this traffic, and no claim of Google ranking or indexing is made.

## Hard release rules

1. Never add a new recommendation/scoring/identity engine for SEO.
2. Keep **0% price weight** in performance ranking; price is an eligibility/reference gate only.
3. Never turn manufacturer model-level facts into proof of exact India variant or hands-on benchmark.
4. Never claim a retailer link is verified buyable merely because it opens Amazon, Flipkart or Croma.
5. Only publish a genuinely differentiated indexable page with at least sufficient source-backed technical substance, one canonical URL, internally crawlable links and a helpful intent.
6. Block deployment on broken public artifacts, unsafe external hosts, missing source links, invalid schema, missing canonical, ranking-contract regression or failed real-browser QA.
7. Measure results in Search Console; **traffic is earned, not automatically delivered by publishing pages**.

## What requires outside access or longitudinal evidence

Google Search Console and GA4 reporting, competitor keyword search-volume estimates, actual Google indexing, live retailer certification, original hands-on reviews, and off-site content distribution cannot be truthfully marked complete by code deployment alone. The site can publish and be testable now, but search engine traffic and earnings must be measured over time.
