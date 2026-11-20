# Coupon World — P0 technical SEO discovery audit (2026-11-13)

**Scope:** read-only source inspection of GitHub `main`; live HTTP/GSC verification incomplete. No production modifications, new engines, rankings, or URL restoration.

## History / guardrails
- Preserve existing approved search-first homepage, research/shop separation, source evidence, exact-variant policy and price-as-budget-only rules.
- Prior SEO cleanup reportedly retained 168 candidate URLs and retired 977 low-value URLs. These are historical figures, **not** proof of current live deployment.
- Never reintroduce retired pages or assume a Google indexed URL based on sitemap presence.

## Source observations (main)
- `robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: https://coupon-world.in/sitemap.xml`. No repository-level blanket crawl block.
- `sitemap.xml`: **114 unique `<loc>` entries**: 1 homepage, 105 `/products/`, 5 `/guides/`, 3 `/seo/`. **Zero `/phones/`, `/compare/`, `/tvs/`, `/accessories/` URLs.** XML includes historical non-tech product paths. This is a checked-in-file observation, not yet a verified production sitemap inventory.
- `index.html`: self-referencing HTTPS canonical, `index, follow`, title/description, visible editorial HTML, phone search links, and `noscript` fallback to guide/phone/compare URLs. Interactive catalogue and search require JavaScript; crawlers' rendered results are not yet verified.
- `scripts/quality_gate.py`: checks sitemap XML, duplicate URLs, origin, homepage presence, robots sitemap declaration and homepage metadata. Missing phones/tvs/accessories sitemap sections only **warn**. Compare and guide/SEO completeness are not explicitly checked. A green CI run cannot establish completeness.
- `python/google_discovery_audit.py`: existing read-only local audit. Reuse this; do not create parallel SEO engine.
- `python/seo_generator.py`, `python/phone_guides.py`, `python/internal_link_engine.py`: existing generation and link infrastructure. Determine build ordering and publish outputs before modifying any.
- `CNAME`: coupon-world.in. Root `404.html` and `_redirects` not found at inspected paths; this alone does not establish live redirect/404 behavior.
- Inspected `phones/index.html`, `phones/under-25000/index.html`, `compare/index.html` and `seo/phone-research-evidence-method.html` were not found as checked-in files. They may be generated during publishing. Verify actual build artifacts.

## Unverified and not to be claimed
- Actual deployed sitemap count (114 vs historical 168), HTTP 200/301/404 status, redirect chains, canonical headers, rendered DOM, sitemap-to-live-page parity, Google indexing and impressions.
- Live URLs `/sitemap.xml`, `/robots.txt`, `/phones/under-25000/` could not be retrieved from this execution environment. This is **not** proof of website outage.

## Next P0 actions and acceptance
1. **Deploy provenance:** inspect GitHub Pages / build workflow, generator ordering and published artifact. Record deployed revision, sitemap checksum/count and path groups. PASS only when build output is matched to the actual public response.
2. **Live HTTP matrix:** fetch homepage, robots, sitemap, /phones/, /phones/under-25000/, /compare/, 3 guide/SEO URLs and a sample of retired URLs. Record status, final URL, content type, canonical, meta robots and JS-off body. Verify retired URLs are real 404/410 or documented correct redirects, not blanket homepage redirects.
3. **Sitemap coverage:** compare *only verified live, indexable, canonical* priority URLs to sitemap; do not insert speculative URLs. Keep old low-value pages retired.
4. **GSC evidence:** export Page indexing reasons, Sitemaps submission status, URL Inspection for priority URLs, and Performance clicks/impressions by page/query. Do not equate indexing with ranking.
5. **Quality gate improvement (separate change after build parity):** validate against generated artifact and fail for absent verified priority URLs, duplicate/noncanonical or nonexistent URLs. Keep legitimate sections optional until their live routes are established.
6. **AI search:** after crawl/indexability fixes, check OAI-SearchBot/Bingbot access and answer-first evidence-backed pages; no promise of citations.

## Current release decision
**HOLD all production SEO changes.** Diagnose build/live parity and GSC before changing sitemap, canonicals, redirects or indexing policy. This document is an audit artifact only.
