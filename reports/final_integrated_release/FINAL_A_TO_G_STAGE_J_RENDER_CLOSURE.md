# Coupon World — Consolidated Phase A–G, Stage-J, Render and GitHub Pages Closure

**Review scope:** existing eight development commits plus the reviewed candidate data package.
**Review date:** 2026-10-15 (Asia/Calcutta).
**Rules applied:** no new engine, ranker, parser, registry, retailer adapter or database; no push or deploy; main worktree and dirty research data preserved.

## A. Current Git and branch state

| Item | Verified value |
|---|---|
| Main worktree | `C:\Users\HP\Documents\projects\couponword-integration` |
| Main HEAD | `b3b6539cf7661766a43934ca3ff00ea74c7b1eb4` |
| Reviewed branch | `release/phase-e-reviewed` |
| Reviewed branch HEAD before this report commit | `4fb3faa1e66415fede7ce02894557fa58ad2f7a9` |
| Common ancestor | `b3b6539cf7661766a43934ca3ff00ea74c7b1eb4` |
| `origin/main` | `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e` |
| Main vs remote | ahead 8, behind 0 |
| Candidate vs remote | ahead 9 after its reviewed package; it contains the eight main commits plus the candidate package |

The eight intended main commits are, in order: `b4c70db`, `25c279d`, `0c5be2f`, `0421a19`, `ab94013`, `78553b1`, `eb73c95`, and `b3b6539`.  The candidate-only package contains stable T5 Pro evidence, its canonical manufacturer mapping, a focused release test, and the reviewed release reports.  No main-worktree files were staged or altered by this review.

The main worktree remains intentionally dirty.  Modified runtime/research JSON includes `data/retail_price_cache.json`, `data/retailer_offers.json`, `data/retailer_product_registry.json`, `data/runtime_shopping_intelligence.json`, and `data/verified_product_evidence_cache.json`.  Untracked discovery/audit JSON, `outputs/`, `phase_e_current.zip`, helper scripts and `reports/master_system_audit/` remain owner data and are excluded from the candidate.

## B. Public Pages security

The repository contains an existing manual `workflow_dispatch` workflow, `.github/workflows/public-pages-artifact.yml`, which builds with `scripts/build_public_pages.py`, uploads the generated artifact and deploys with `actions/deploy-pages@v4`.  It requests only `contents: read`, `pages: write` and `id-token: write`.  The builder allow-list contains public HTML/CSS/JS, public catalog JSON, approved product/SEO assets and `CNAME`, `robots.txt` and `sitemap.xml`; it rejects `admin.html`, `validator.html`, Python, reports, outputs, backups, ZIP files and secrets.

The live site is not using that reviewed artifact yet.  The public GitHub API showed zero runs for the manual allow-listed workflow and the older dynamic `pages-build-deployment` workflow had its latest successful run from `main` at SHA `5167712b369c81ab85779819763eee6e9b90a831` (run `38022191254`, 2026-10-10).  This explains the live result:

| Live path | Observed result | Security meaning |
|---|---:|---|
| `/` | HTTP 200 | public site works |
| `/sitemap.xml` | HTTP 200 | public SEO asset works |
| `/coupons.json` | HTTP 200 | public catalog asset works |
| `/admin.html` | HTTP 200 | private review shell is publicly served |
| `/validator.html` | HTTP 200 | internal validator is publicly served |
| `/data/retailer_offers.json` | HTTP 200 | internal offer data is publicly served |
| `/data/verified_product_evidence_cache.json` | HTTP 200 | internal evidence cache is publicly served |
| `/reports/phase_e/final_certification.md` | HTTP 404 | this path was not exposed |
| `/phase_e_current.zip` | HTTP 404 | this ZIP was not exposed |

Inspection of the local admin surface found a read-only HTML shell: no browser-side `fetch`, XHR or `axios` mutation path and no score-writing client operation.  API routes expose no POST/PUT/PATCH/DELETE mutation route.  That limits the demonstrated integrity risk, but the confidentiality risk is real because internal evidence and offers are publicly downloadable.  Local artifact exclusion tests pass; live exclusion is **BLOCKED** until the Pages source is switched to the allow-listed Actions artifact (or Pages is disabled as an owner-approved containment) and live HTTP checks show 404 for the internal paths.

**Urgent owner containment:** stop legacy root/branch publishing or switch the Pages source to GitHub Actions, run the reviewed workflow from the intended candidate, and capture the workflow/deployed SHA.  No live fix was executed in this task.

## C. Render infrastructure

The bounded live health check returned HTTP 200 from `https://couponword.onrender.com/health` with:

```json
{"revision":"2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e","service":"coupon-world-shopping-intelligence","status":"ok"}
```

The live API smoke for `mobile under 30000` also returned HTTP 200 and a valid response.  It is running the remote baseline SHA, not the reviewed candidate.

| Setting | Current value | Verified? | Required action |
|---|---|---:|---|
| Deployed revision | `2db6534...` | YES | deploy only after separate approval |
| Service/branch | not exposed by health | NO | owner checks Render dashboard |
| Plan | not exposed | NO | owner checks; no plan change assumed |
| Build command | no tracked `render.yaml`, `Procfile` or Docker file | NO | record dashboard command |
| Start command | Gunicorn is visible in response headers; exact command unknown | PARTIAL | record exact command |
| Environment names | `TAVILY_API_KEY`, `GEMINI_API_KEY`, `COUPONWORLD_LIVE_FAST`, `RENDER_GIT_COMMIT` are code/config names; values not collected | PARTIAL | verify names only and secret ownership |
| Persistent disk | unknown | NO | verify service disk and mount path |
| Restart persistence | no receipt | NO | backup, restart/redeploy test, restore/rollback plan |
| Offer scheduler | no verified six-hour mobile refresh | NO | choose an authorized service-owned or protected refresh path |

Runtime paths in the existing code are `data/verified_product_evidence_cache.json`, `data/retailer_product_registry.json` and `data/retailer_offers.json`.  Product evidence also has the packaged fallback `data/phase_e_release_evidence.json`.  Offer writes are atomic in `python/retailer_offer_store.py`; evidence writes use a temporary replace in `python/product_evidence_store.py`.  These paths are local JSON stores, so persistence across a Render restart is unverified and must not be inferred from a successful boot.

## D. Offer refresh and source access

Existing code paths are `evidence_offer_updater.py`, `python/retail_price_evidence.py`, `python/retailer_offer_store.py`, `python/retailer_connector_manager.py`, `python/multi_retailer_orchestrator.py` and `python/shopping_intelligence_pipeline.py`.  The allowed source families are Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales and the approved manufacturer stores.  The code has source allow-lists and a six-hour freshness rule (`6 * 60 * 60` seconds), but code support is not operational authorization or proof of a running refresh.

| Requirement | Local finding | Status |
|---|---|---|
| exact SKU/variant association | existing identity/offer gates and separate manufacturer SKU/ASIN fields | LOCAL PASS |
| source-specific current price | expired observations are rejected; no current T5 offer is released | LOCAL PASS / LIVE UNVERIFIED |
| persistence | atomic file writes exist; shared durable production store is unknown | BLOCKED |
| scheduler/cadence | no configured six-hour mobile-offer scheduler found | BLOCKED |
| API visibility | API reads the existing offer store in local tests and live baseline | LOCAL PASS / CANDIDATE UNVERIFIED |
| retries, failures, monitoring | adapter code exists; operational receipts/alerts absent | BLOCKED |

The smallest safe operational design is one authorized writer using the existing updater and offer store, backed by the same durable store read by the web service.  A separate cron service must not write an isolated local JSON copy.  No CAPTCHA bypass, search-card price, launch price or unverified credential was used.  Until source authorization, storage, cadence, stale counts, failure timestamps and alerting are evidenced, automatic refresh is **BLOCKED**.

## E. Mobile coverage

The existing reports and frozen receipts reconcile to the following inventory boundaries:

| Funnel stage | Count/status | Interpretation |
|---|---:|---|
| research seed rows | 187 | leads only; not eligibility |
| public catalogue mobile rows | 40 (105 total public catalogue rows) | catalogue surface, not all verified |
| canonical mobile IDs | 34 (37 registry records) | exact identity registry |
| matching durable official evidence | 13 | verified product knowledge in the durable stores |
| durable release evidence | 12 records in the reviewed package | candidate release subset |
| stored retailer offers | 8 records, 3 old in-stock observations | volatile; freshness still applies |
| frozen exact offers used in replay | 4 | bounded certification fixture, not live coverage |
| Phase-G controlled admission | 1 admitted (vivo T5 Pro); other selected candidates blocked | no mass admission claimed |

The reviewed stable package contains exact vivo T5 Pro 5G, `cw-mobile-96`, 8GB/128GB, manufacturer SKU `19410` and Amazon ASIN `B0H6F4KZGF`, with source URL `https://shop.vivo.com/in/product/10344?skuId=19410`.  Its observed ₹41,999 offer at `2026-10-14T17:45:11Z` is historical and outside the six-hour freshness window; it is intentionally not included as a current offer.  Manufacturer SKU and ASIN remain separate identifiers.  Product DNA survives offer expiry.

Budget-specific rankable coverage is only certified where a frozen receipt exists.  The ₹30k frozen replay has 34 candidates and 2 eligible results (Lava Bold N2 Lite and Lava Virat V1); 30 candidates have unknown/expired price and 2 are over budget.  The saved 100-query baseline had 41 scored and 59 honest incomplete responses.  A complete current rankable inventory for every requested premium band is **not certified** because current offers are sparse.

## F. Phase A–G and Stage-J matrix

| Phase | Local status | Live status | Completed | Remaining | Next action |
|---|---|---|---|---|---|
| A — Production Parity | PARTIAL | UNVERIFIED | local backend/frontend foundation and release review | live revision/data parity | verify approved SHA, Render settings and persistent data |
| B — Intelligence UI | PARTIAL | PARTIAL | local API/trace/score regressions | live frontend-to-candidate API parity | smoke test candidate revision |
| C — Analytics/SEO | PARTIAL | PARTIAL | sitemap, schema and public assets exist | indexing, conversion and revenue proof | owner analytics verification |
| D — Mobile Knowledge Coverage | PARTIAL | INCOMPLETE | identity/evidence pipeline and selected admissions | 187 seeds are not a verified catalogue; offers sparse | authorized evidence and offer coverage batches |
| E — Quality/Certification | LOCAL PASS (technical scope) | INCOMPLETE | parser, Gate-3 and frozen determinism receipts | market quality and live parity | preserve fixture gap; verify live release |
| F — SEO/Growth | BLOCKED/UNDEFINED | UNVERIFIED | no authoritative completion evidence | growth acceptance not established | define and approve F acceptance separately |
| G — Mobile/Retailer Integration | PARTIAL | BLOCKED | reusable admission/atomic persistence path | durable storage, refresh operations and premium coverage | verify Render operations and authorized refresh |
| Stage-J — final stability | PARTIAL | BLOCKED | focused local regressions and deterministic replays | live artifact/security and production smoke | complete live Pages/Render checks |

## G. Test and verification ledger

| Test/receipt | Executed | PASS | FAIL | Incomplete/skip | Evidence |
|---|---:|---:|---:|---:|---|
| parser corpus | 1000 | 1000 | 0 | 0 | saved Phase-E receipt |
| original Gate-3 | 14 | 14 | 0 | 0 | saved Gate-3 receipt |
| baseline unit/integration suite | 172 reported cases | 170 | 0 | 2 optional SKIP | existing certification receipt |
| frozen 30k spelling replay | 4 | 4 deterministic | 0 | 0 | existing frozen replay |
| focused candidate/release set | 37 | 36 | 1 | 0 | one preserved historical fixture `FIXTURE_GAP` |
| reviewed T5 Pro release guards | 4 | 4 | 0 | 0 | `test_phase_e_reviewed_t5_pro_release.py` |
| local public artifact exclusion | bounded | PASS | 0 | 0 | allow-list builder/test |
| live Pages security | bounded HTTP | 0 | exposure observed | BLOCKED | admin, validator and internal JSON returned 200 |
| Render `/health` and API smoke | bounded HTTP | 2 endpoints 200 | 0 | candidate revision not live | remote revision `2db6534...` |
| saved 100-query baseline | 100 | 100 deterministic | 0 technical | 41 scored, 59 honest incomplete | market usefulness not independently reviewed |

The historical non-catalogue three-result fixture remains FAIL/FIXTURE_GAP.  Its approved genuine two-result successor passes; this is not a retrospective pass and remains a visible release limitation.

## H. Changes actually made and release contents

No recommendation, scoring, intent, discovery, identity or retailer-engine change was made in this closure turn.  The reviewed candidate-only commit `4fb3faa1e66415fede7ce02894557fa58ad2f7a9` contains:

- `data/phase_e_release_evidence.json` — durable exact vivo T5 Pro evidence;
- `data/retailer_product_registry.json` — exact manufacturer mapping with SKU `19410` and ASIN `B0H6F4KZGF` kept separate;
- `test_phase_e_reviewed_t5_pro_release.py` — four focused guards;
- `reports/release_and_query_consistency/FINAL_REVIEWED_RELEASE_PACKAGE.md`;
- `reports/release_and_query_consistency/REVIEWED_STABLE_DATA_DIFF.md`.

The eight existing main commits remain unchanged.  Their source path is the authoritative existing flow: intent → discovery → canonical identity → official evidence → exact offer/freshness → eligibility → score/rank → explanation/API serialization.  No duplicate path was introduced.  Rollback of the candidate source/data package is the remote baseline `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`, subject to restoring compatible persistent data.

## I. Release manifest

**Intended candidate:** `release/phase-e-reviewed` at `4fb3faa1e66415fede7ce02894557fa58ad2f7a9` before this report-only commit, plus this report when committed.  It contains the eight reviewed commits from `b4c70db` through `b3b6539` and the stable-data package.

**Backend inputs:** existing Python source, `requirements.txt`, approved stable evidence, canonical registry and runtime configuration by name only.  `python/shopping_api.py` is the entry point; the exact Render dashboard start command is not tracked and remains an owner verification item.

**Pages inputs:** `.github/workflows/public-pages-artifact.yml`, `scripts/build_public_pages.py`, and the allow-listed public assets.  The workflow must be run manually from the approved candidate.  Repository-root publishing is not an acceptable release source.

**Excluded:** dirty runtime caches, discovery/audit JSON, `outputs/`, backups, `phase_e_current.zip`, helper audit scripts, `cw-mobile-test`, reports not explicitly included in the reviewed candidate, internal admin/validator HTML and all secrets.

**Infrastructure:** persistent storage, initialization/migration, offer refresh scheduler, source authorization, monitoring and alerting are not proven in Git and must be verified in Render/owner-controlled operations.

## J. Owner action list

1. **Contain Pages exposure (urgent, no code change):** set GitHub Pages publishing to GitHub Actions or disable Pages until the safe workflow is run. This changes publishing configuration, not recommendation logic, and normally has no code cost. Capture the workflow run/artifact SHA and live 404 checks for `/admin.html`, `/validator.html`, `/data/retailer_offers.json` and `/data/verified_product_evidence_cache.json`.
2. **Verify Render dashboard:** record service plan, repository/branch, auto-deploy setting, build command, exact Gunicorn start command, environment variable names, disk/mount and current deployed SHA. No paid disk or plan change is approved by this report.
3. **Authorize storage/refresh operations:** decide whether the existing service may use a durable store at a documented mount path and choose an authorized service-owned/protected refresh execution path. Capture backup, restart/redeploy persistence, last-success/last-failure timestamps, stale counts and alerting. Do not use a separate cron-local JSON copy.
4. **Authorize release separately:** after the above evidence is reviewed, authorize pushing the exact candidate and running the existing Pages workflow/backend deployment. Capture backend `/health` revision, frontend/API smoke, fresh permitted offer receipt and rollback readiness.

## K. Final decisions

| Gate | Decision |
|---|---|
| Phase A | PARTIAL |
| Phase B | PARTIAL |
| Phase C | PARTIAL |
| Phase D | BLOCKED/INCOMPLETE |
| Phase E | LOCAL TECHNICAL PASS / MARKET QUALITY INCOMPLETE |
| Phase F | BLOCKED/UNDEFINED |
| Phase G | BLOCKED/PARTIAL |
| Stage-J local regression | PARTIAL (36/37 focused; historical fixture remains visible) |
| GitHub Pages security | LOCAL PASS / LIVE BLOCKED |
| Render data persistence | UNVERIFIED/BLOCKED |
| Automatic price refresh | BLOCKED |
| Independent market quality | NOT CERTIFIED |
| Release candidate | READY FOR REVIEW LOCALLY |
| Production | NO-GO |

**Primary remaining blocker:** the live Pages site is still serving the legacy root/dynamic artifact at the old SHA and exposes `admin.html`, `validator.html` and internal evidence/offer JSON; the reviewed allow-listed artifact has not been run live.

**Smallest owner action set:** (1) contain/switch Pages publishing and verify the artifact, (2) verify Render storage/start/branch and authorize one durable refresh path, and (3) separately authorize the exact candidate push/deploy followed by live smoke tests.

**Exact source/data ready for review:** the eight main commits through `b3b6539` plus reviewed candidate commit `4fb3faa` and this report-only commit once created.  Main dirty research/cache files are excluded and preserved.

**Evidence required before declaring live:** Pages workflow run and deployed SHA; live 404s for all internal paths; Render `/health` revision equal to the approved candidate; persistent-store restart receipt; authorized fresh offer-refresh receipt with timestamps and availability; frontend/API/score-explanation smoke; and a documented rollback result.
