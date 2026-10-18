# Coupon-World consolidated release candidate

Date: 2026-10-18
Base: `origin/main` (`e6fbf8b307c942045035b92d35492f3394bb5859`)
Integrated branch: `release/couponworld-consolidated-20261018`
Pre-report source HEAD: `0472fd39186e7ff17f2e88bdf2f0095bd1e9fdd6`

## Integration scope

The candidate was created in a new clean worktree from `origin/main` and
fast-forwarded to `phase-d-coverage`. The branch graph is linear, so the
security/retailer, ranking and Phase-D commits were retained once through
their existing ancestry; no stale security-audit or reviewed-release commits
were cherry-picked.

The 17 source commits entering this candidate are:

```text
fdd77e4 security: harden public links, API errors and retailer redirects
f6a54fb security: close redirect and policy gaps
13167bc fix: escape verified retailer button URLs
560033a fix: complete product pages and neutralize public retailer text
a37b686 style: refresh static product page presentation
c29d564 config: update Amazon affiliate tag
dc7f6dd fix: separate budget-band recommendations from value options
e5d9dce fix: correct budget band classification contract
ad283e3 phase-d: record verified mobile coverage batch
6115f02 phase-d: persist verified DNA admission state
9f2b8c1 phase-d: admit verified mobile DNA batch
4bd00eb docs: add Phase D mobile inventory status
b092d57 feat: add resumable India mobile coverage manifests
64bbf05 fix: use existing fresh offer gate in coverage queue
068ee73 feat: execute verified mobile DNA admissions
a130d28 phase-d: ingest verified official mobile evidence
0472fd3 fix: recover bounded mobile official sources
```

The older `security-audit-20261016` and `release/phase-e-reviewed` tips are
historical/report branches and are not replayed over the newer linear source.

## Feature gates

| Gate | Local result | Evidence |
|---|---|---|
| Integration ancestry | PASS | `origin/main` is an ancestor; candidate is 17 commits ahead before this report commit. |
| Security | PASS | API errors are generic, public URLs are escaped and scheme-checked, retailer redirects authorize each hop, CORS is restricted, and security regression tests pass. |
| Retailer buttons | PASS | Existing Amazon/Flipkart/Croma rendering and in-stock-only button gates are covered by retailer/frontend tests. |
| Ranking contract | PASS | Hard budget remains enforced; 80%–100% primary band and separate value section are covered without changing score weights. |
| Phase-D data | PASS locally | Clean checkout contains 27 Product DNA records and 42 official evidence records; no dirty cache is required to import the API. |
| Clean boot | PASS | `shopping_api` imports from the clean worktree; all tracked Python modules compile. |
| Pages security | PASS locally | `scripts/build_public_pages.py` produced 128 files and excluded `admin.html`, `validator.html`, Python, reports, outputs, backups, caches, secrets and ZIP/credential-like files. Workflow is manual `workflow_dispatch` and uses the allow-listed artifact plus `deploy-pages`. |

## Durable data and offer status

Tracked durable records in the clean candidate:

- `data/mobile_intelligence_repository.json`: 27 Product DNA records.
- `data/verified_product_evidence_cache.json`: 42 evidence records.
- `data/retailer_offers.json`: 7 historical offer rows; two rows have a raw
  `in_stock` label, but their August observations are outside the six-hour
  freshness gate. `find_fresh_verified_offer()` therefore returns **0 valid
  current offers** at evaluation time.
- No current price or retailer button is claimed from stale/unknown offers.

The uncommitted research manifests, runtime caches, discovery/sitemap caches,
audit outputs, ZIP files and backups in the owner worktrees were not copied or
staged. They remain untouched in their original worktrees.

## Verification performed

- Focused security, retailer, ranking, Phase-D, Phase-E and API/frontend
  regressions: **128 PASS, 0 FAIL, 0 ERROR**.
- Python compilation (`python/`): **PASS**.
- JavaScript syntax (`app.js`, `buying-guides.js`): **PASS**.
- Public artifact build and forbidden-file scan: **PASS**.
- Git whitespace check: **PASS**.
- No live Render or GitHub Pages deployment was performed or claimed.

## Operational and release risks

1. Current durable offer evidence is stale, so production market-quality
   recommendations and clickable retailer choices require an authorized
   refresh process and persistent storage. This is a data/operations blocker,
   not a reason to weaken eligibility.
2. The scheduled `.github/workflows/bot.yml` has `contents: write` and can push
   `coupons.json`; it is not a Pages or Render deployment trigger, but it is a
   repository-integrity risk that should remain disabled or be separately
   reviewed before production use.
3. Render and live Pages revisions were not queried in this local-only run.
   Live parity and smoke checks remain unverified.

## Release decision

This is a **reviewable local/staging candidate**. It is **not production-ready**
until the owner verifies the offer-refresh/persistent-store arrangement and
performs authorized live Render and Pages smoke tests. No push, merge, deploy,
reset or cache cleanup was performed.

Rollback is the base SHA `e6fbf8b307c942045035b92d35492f3394bb5859`; the release
can be reverted without touching the preserved dirty research worktrees.
