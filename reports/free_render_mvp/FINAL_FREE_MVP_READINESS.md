# Coupon World — Free Render MVP Readiness

**Scope:** reliable verified-product MVP on Render Free.  Current retailer-price operations are deliberately deferred.  No new engine, database, paid infrastructure, push or deploy was performed.

## 1. Git state and ancestry

| Item | Value |
|---|---|
| Main HEAD | `b3b6539cf7661766a43934ca3ff00ea74c7b1eb4` |
| `origin/main` | `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e` |
| Reviewed candidate before this report | `ea381a2b358a02efaa1db743a7c6d9021acb9126` |
| Candidate branch | `release/phase-e-reviewed` |
| Candidate commits ahead of remote before this report | 10 |
| Common ancestor of main and candidate | `b3b6539cf7661766a43934ca3ff00ea74c7b1eb4` |

The main worktree remains dirty by design. Runtime caches, research JSON, reports, backups, ZIP files and helper scripts were not staged. Candidate generated `outputs/` and runtime cache changes are also excluded from the release commit.

## 2. Stable Product DNA

The existing bundled evidence loader merges the tracked `data/phase_e_release_evidence.json` into the normal evidence store without hydrating prices. The clean candidate contains 13 bundled official-evidence records, 17 records in the ordinary evidence cache and 37 registry product records. The bundle is filtered by existing resolver/fetch/identity/variant checks; research-seed presence is not enough.

The reviewed vivo record is preserved exactly:

- canonical product: `cw-mobile-96`
- model: vivo T5 Pro 5G
- physical variant: 8GB RAM / 128GB storage
- Amazon ASIN: `B0H6F4KZGF`
- manufacturer SKU: `19410`
- official URL: `https://shop.vivo.com/in/product/10344?skuId=19410`

The ASIN and manufacturer SKU remain separate registry identifiers. The clean tracked boot test retrieved the exact variant and SKU without relying on the main worktree's dirty cache.

## 3. Offers and Free Render behavior

The candidate's tracked offer store has seven historical records and **zero currently fresh offers at the 2026-10-16 evaluation time**. This is an honest MVP state; no expired observation is released as a current price.

The existing `find_fresh_verified_offer()` gate requires:

- exact canonical product, brand, model and physical variant;
- positive numeric price;
- approved source URL;
- `in_stock` availability;
- valid observation timestamp no older than 21,600 seconds;
- selected manufacturer SKU binding where applicable.

Expired and out-of-stock offers therefore do not enter a budget ranking. Product DNA remains available after offer expiry. `add_verified_offer()` replaces the same `(product_id, retailer, retailer_product_id)` key, and `save_offer_database()` writes a flushed temporary file followed by atomic replacement. No runtime write is assumed to survive Render Free sleep, restart or redeploy.

Render settings supplied by the owner are:

- Free plan, repository root, `main` branch;
- build: `pip install -r requirements.txt`;
- start: `gunicorn --chdir python shopping_api:app --timeout 120`;
- pre-deploy empty, auto-deploy off;
- last confirmed live SHA: `2db6534`.

The service may read packaged Product DNA after boot, but it cannot provide reliable durable mutable offers on the Free filesystem. No background refresh was added and no uncontrolled Gunicorn-worker scheduler is allowed.

## 4. API and frontend contract

The existing API/pipeline path remains authoritative. A bounded clean-candidate API smoke returned HTTP 200 with the existing response fields, and a missing/volatile-offer situation does not turn into a server error. The contract retains separate intent, candidate, eligibility, fit, quality and completion fields.

The intended user-facing states are:

- “Official specifications verified. Current price unavailable.”
- “Only two currently verified qualifying offers are available.”
- “Unable to confirm a current offer within your budget.”

Unknown price is never used to satisfy a numeric budget. No Top-3 is forced. No scoring weights, thresholds, query signatures or ranking behavior were changed.

## 5. Focused test results

The following direct `unittest` files were run independently in the reviewed candidate:

| Test file | Result |
|---|---:|
| `test_phase_e_release_evidence.py` | 7/7 PASS |
| `test_phase_e_manufacturer_offer_admission.py` | 4/4 PASS |
| `test_phase_e_reviewed_t5_pro_release.py` | 4/4 PASS |
| `test_phase_e_query_consistency.py` | 4/4 PASS |
| `test_phase_e_selected_sku.py` | 3/3 PASS |
| `test_phase_g_offer_store_persistence.py` | 2/2 PASS |
| **Focused total** | **24/24 PASS** |

Additional saved acceptance remains valid: parser 1000/1000, original Gate-3 14/14, baseline 170 PASS / 0 FAIL / 0 ERROR / 2 optional SKIP, frozen determinism 1000/1000, and the approved two-result successor. The original historical three-result fixture remains visible as `FAIL / FIXTURE_GAP`; it was not skipped or rewritten.

The clean tracked boot simulation passed: exact T5 Pro evidence loaded, Vivo SKU `19410` resolved, and `/health` returned HTTP 200. Local Pages artifact security checks passed, and the owner-provided live URL checks confirm the secured Pages artifact. No live retailer-price claim was made.

## 6. Acceptance decisions

| Gate | Decision | Evidence |
|---|---|---|
| Stable Product DNA | PASS | 13-record bundle, exact T5 Pro retrieval in clean candidate |
| Free Render boot | PASS | clean tracked boot and API health smoke |
| Expired-offer safety | PASS | four T5 release guards and offer-admission tests |
| Honest incomplete behavior | PASS | eligibility/freshness gates and API contract preserved |
| Exact variant safety | PASS | identity, selected-SKU and release tests |
| Query determinism | PASS | saved 30k spelling and 1000-query frozen receipts |
| Frontend/API compatibility | PASS locally | existing contract and API smoke; candidate not live |
| GitHub Pages security | PASS per owner live URL checks | admin, validator and internal registry paths inaccessible |
| Stage-J regressions | PARTIAL | focused 24/24 PASS, historical fixture remains FAIL/FIXTURE_GAP |

## 7. Final MVP release manifest

Release the reviewed candidate source/data commits through the current candidate tip, plus this report-only commit when reviewed. Include the existing backend source, `requirements.txt`, `data/phase_e_release_evidence.json`, canonical registry and unchanged baseline offer store. Do not add dirty runtime caches, research/audit JSON, `outputs/`, backups, ZIP files, `cw-mobile-test`, secrets or generated reports.

Required environment variable names remain `RENDER_GIT_COMMIT`, `TAVILY_API_KEY`, `GEMINI_API_KEY` and `COUPONWORLD_LIVE_FAST`; no secret values are included. The Render start command is the owner-confirmed Gunicorn command above. Rollback target is `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`, with any runtime files restored separately if they ever exist.

## 8. Deferred live-price operations

The MVP does not certify current retailer prices. There is no paid disk, no shared database and no approved six-hour refresh scheduler. A GitHub Actions job cannot reliably write a Render Free local filesystem, and a separate Render Cron service would have its own filesystem. The safe Free-tier behavior is to let offers expire and return an honest incomplete response.

Live price operations require a future owner decision about permitted retailer access, source-specific TTLs, a single writer, persistence and monitoring. That is outside this Free MVP release and must not be emulated with bundled historical prices.

## 9. Final acceptance

- **STABLE PRODUCT DNA:** PASS
- **FREE RENDER BOOT:** PASS
- **EXPIRED OFFER SAFETY:** PASS
- **HONEST INCOMPLETE:** PASS
- **EXACT VARIANT SAFETY:** PASS
- **QUERY DETERMINISM:** PASS
- **FRONTEND/API COMPATIBILITY:** PASS locally
- **PAGES SECURITY:** PASS per supplied live checks
- **STAGE-J REGRESSIONS:** PARTIAL
- **FREE MVP RELEASE CANDIDATE:** READY for owner review; not deployed
- **LIVE RELEASE:** NOT AUTHORIZED
- **LIVE PRICE OPERATIONS:** DEFERRED
- **MARKET QUALITY 90–95%:** NOT CERTIFIED

### A. Work completed in this run

Verified clean-candidate Product DNA loading, exact T5 Pro identity/SKU separation, expiry and idempotency guards, API boot behavior, six focused test files (24/24 PASS), and the Free-tier release boundary. No engine or infrastructure code was changed.

### B. Exact remaining defects

There is no reproduced recommendation-engine defect for this MVP scope. The remaining operational limitations are Free Render's ephemeral filesystem, no verified offer-refresh scheduler, no current buyable offer in the candidate's tracked store at evaluation time, and the preserved historical fixture gap.

### C. Exact owner authorization needed for future release

Authorize review and deployment of the candidate only after confirming the approved Pages artifact, backend SHA and rollback receipt. Current-price operations additionally require a separate decision on permitted retailer access and durable storage; this report does not authorize paid services or a scheduler.

### D. Smallest safe next step

Review this report and the candidate diff, then perform one owner-approved Free-tier staging smoke using packaged Product DNA. Keep current-price claims disabled until a permitted fresh offer is independently observed.
