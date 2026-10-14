# Coupon-World Phase-G Final System Integration Closure

Date: 2026-10-15
Scope: existing Phase-G architecture only; no new engine, database, ranker or discovery path.

## A. Verified root causes

| Root cause | Affected modules | Proof | Correction / state |
|---|---|---|---|
| Research/discovery records are not automatically promoted into one durable evidence lifecycle | `market_discovery.py`, `official_source_resolver.py`, `official_spec_extractor.py`, `product_evidence_store.py`, `retailer_product_registry.py` | The controlled 15-variant batch admitted only vivo T5 Pro; 6 variants had evidence but no fresh buyable offer and 8 lacked exact durable evidence | Existing exact-variant admission path is reusable; external evidence/offer coverage remains incomplete |
| Current offers are sparse or expired | `retail_price_evidence.py`, `retailer_offer_store.py`, `shopping_intelligence_pipeline.py` | The six-hour gate leaves one fresh buyable mobile offer in the current working stores; the saved frozen replay has four historical positive offers | Kept fail-closed freshness and availability rules |
| Offer-store writes were vulnerable to a truncated JSON after interruption | `retailer_offer_store.py` | `save_offer_database()` previously overwrote the target directly | Atomic temp-file flush and replace added in local commit `ab94013`; isolated persistence and idempotency tests pass |
| No verified six-hour production refresh controller | `.github/workflows/*`, `retailer_connector_manager.py`, `multi_retailer_orchestrator.py` | Existing workflows are coupon/catalogue/manual Pages jobs; no scheduled exact-offer refresh, shared persistent store, monitor or alert receipt exists | BLOCKED on scheduler, source authorization and persistent production storage |
| Determinism is not market usefulness | `phase_e_offline_certification.py`, saved 100-query receipt | 100/100 deterministic, but 41 scored and 59 honest incomplete; no independent reviewed usefulness oracle | Reported as provisional execution evidence, not quality certification |

## B. Implemented repairs

The reviewed local code commits are:

- `b4c70db` — frozen Phase-E offer handoff and score replay
- `25c279d` — official mobile source and manufacturer-offer gates
- `0c5be2f` — exact manufacturer-offer admission and fallback
- `0421a19` — verified manufacturer offers in API traces
- `ab94013` — atomic retailer-offer persistence and isolated tests
- report-only closure commit — this authoritative Phase-G closure report

The new repair changes only `python/retailer_offer_store.py` and adds
`test_phase_g_offer_store_persistence.py`. The store now writes a complete,
flushed temporary JSON file and atomically replaces the authoritative file.
Repeated exact admission remains one record.

Focused integration result: **51/51 PASS**, including identity, selected SKU,
official evidence, price freshness, API trace, frontend offer rendering,
frozen replay guards and the new persistence tests. `git diff --check` passes.

## C. Actual data funnel

Historical comparable baseline:

- Research rows: **187**
- Catalogue mobile rows: **40**
- Canonical mobile IDs: **34**
- Exact catalogue-linked official evidence records: **13**
- Frozen positive offer records: **4**

Current working-store read-only count:

- Canonical mobile IDs: **34** (37 registry keys include three non-mobile products)
- Evidence records in cache: **29 total; 13 linked to current mobile catalogue rows**
- Retailer-offer records: **9 total**, including test/history records
- Fresh in-stock exact mobile offers under the six-hour gate: **1** (`cw-mobile-96`)

Controlled 15-variant promotion batch:

- Durable current-offer admission: **1/15** — vivo T5 Pro 8/128
- Exact evidence present but no fresh buyable offer: **6/15**
- Exact durable evidence missing: **8/15**
- No fabricated specifications, prices or stock states

Current live-gate rankable count by budget, using only fresh in-stock offers:

| Budget | Rankable variants |
|---:|---:|
| ₹10k | 0 |
| ₹20k | 0 |
| ₹30k | 0 |
| ₹40k | 0 |
| ₹50k | 1 |
| ₹1.2 lakh | 1 |
| ₹1.5 lakh | 1 |

The saved frozen catalogue scope is different: it previously returned two
under ₹10k–₹30k and three under ₹40k–₹50k. Those frozen results are not live
price proof.

## D. Refresh operations

| Source | Access | TTL/state | Configured job | Persistent output | Monitoring |
|---|---|---|---|---|---|
| Amazon | Existing connector; account/API agreement not verified here | Source-specific contract must be confirmed; generic six-hour gate is not sufficient proof | No active six-hour job found | Not proven across restart/redeploy | None proven |
| Flipkart | Existing connector | Six-hour application gate | No active six-hour job found | Not proven across restart/redeploy | None proven |
| First-party vivo | Exact public selected-SKU JSON-LD used for T5 Pro | Six-hour application gate; exact SKU binding | No refresh scheduler | Local JSON only | None proven |
| Croma/other retailers | Parser support only where present | No active production connector proven | None | None proven | None |

The existing connectors and `MultiRetailerOrchestrator.run(write=True)` are
usable building blocks. Activation still requires an authorized scheduler,
source-specific access rules, atomic shared persistence, overlap protection,
run receipts and alerting. This is an infrastructure/authorization blocker,
not a safe local code assumption.

## E. Recommendation quality

Saved frozen 100-query execution:

- Executed: **100/100**
- Scored responses: **41/100**
- Honest incomplete responses: **59/100**
- Technical failures: **0/100**
- Deterministic semantic matches: **100/100**
- Returned recommendation rows checked for budget safety: **87/87**, violations **0**
- Independently reviewed useful responses: **0/100 certified**
- Market-quality target ≥90%: **NOT CERTIFIED**
- Market-quality target ≥95%: **NOT CERTIFIED**

No independent expected-answer set was available for the 100 cases. The 41
scored responses are therefore provisional engine executions, not proof of
market-best recommendations.

The existing scoring contract remains `capability-with-separate-evidence-v1`:
Quality Score excludes budget, final Fit includes evidence coverage, and sort
order is Quality Score → quality evidence coverage → Fit → stable identity.
No weights or thresholds were changed.

## F. Release manifest

Tested source HEAD before the report-only commit: `ab94013`
Remote baseline: `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`
Local commits ahead of `origin/main`: **6**

Release source files include the five commits above and the existing tested
pipeline modules:

- `python/market_discovery.py`
- `python/official_source_resolver.py`
- `python/official_spec_extractor.py`
- `python/product_evidence_store.py`
- `python/retailer_product_registry.py`
- `python/retail_price_evidence.py`
- `python/retailer_offer_store.py`
- `python/retailer_connector_manager.py`
- `python/multi_retailer_orchestrator.py`
- `python/shopping_intelligence_pipeline.py`
- `python/weighted_fit_engine.py`

Required stable T5 Pro records are currently local working-tree data, not in
the five commits:

- `data/verified_product_evidence_cache.json`
- `data/retailer_product_registry.json`

The current ₹41,999 offer is volatile and must be refreshed before being
treated as a production current offer:

- `data/retailer_offers.json`

Caches, runtime JSON, reports, audit outputs, ZIP files and backups are
excluded from a release unless explicitly reviewed. The working tree contains
such uncommitted files and they were preserved.

Configuration names identified in the code include `RENDER_GIT_COMMIT`,
`TAVILY_API_KEY` and `GEMINI_API_KEY`; values are not included in this report.
Render persistent storage, scheduler ownership and deployed SHA are unknown.

## G. Final acceptance matrix

| Gate | Result |
|---|---|
| Product admission reusable | **PASS, one verified cross-source reference path** |
| Canonical identity | **PASS for admitted variants; catalogue coverage incomplete** |
| Durable official knowledge | **PARTIAL** |
| Retailer-offer promotion | **PARTIAL** |
| Current-offer integrity | **PASS for guarded records** |
| Refresh operations | **BLOCKED** |
| Production data persistence | **UNVERIFIED** |
| Scoring transparency | **PASS** |
| Determinism | **PASS for saved frozen scopes** |
| Market quality ≥90% | **NOT CERTIFIED** |
| Market quality ≥95% | **NOT CERTIFIED** |
| Production release | **NO-GO** |

## H. Exact remaining blockers

1. **Durable release data** — the T5 Pro evidence and registry records are
   uncommitted. Owner action: review and commit only the exact stable records;
   evidence: clean-checkout admission test using those records.
2. **Current-offer operations** — no authorized six-hour scheduler, shared
   persistent store, monitoring or alerting is proven. Owner action: select an
   authorized scheduler/storage arrangement and provide one successful refresh
   plus API-read receipt.
3. **Market coverage** — T5x 8/256 is currently out of stock; Nord CE6 8/256
   lacks approved official evidence and a current offer. Owner action: obtain
   exact permitted evidence and buyable offers, or retain them blocked.
4. **Independent usefulness evaluation** — no reviewed 100-query oracle exists.
   Owner action: approve a frozen rubric and independent reference set, then
   measure usefulness without excluding failed cases.
5. **Deployment parity** — local HEAD is ahead of GitHub and Render revision is
   unknown. Owner action: after explicit release approval, push the reviewed
   commits and collect live API/frontend/Pages smoke receipts.

## Final decision

**PHASE-G TECHNICAL INTEGRATION: PARTIAL**
**PHASE-G OPERATIONAL READINESS: BLOCKED**
**MARKET QUALITY TARGET: NOT CERTIFIED**
**PRODUCTION RELEASE READINESS: NO-GO**

**Primary remaining blocker:** no authorized, persistent, observable current-offer refresh lifecycle, and the verified T5 Pro durable records are still local-only.

No push, deploy or Phase-F work was performed.
