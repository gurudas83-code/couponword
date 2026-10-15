# Final reviewed release package

## Baseline and candidate

- Source baseline: b3b6539cf7661766a43934ca3ff00ea74c7b1eb4
- Remote baseline: 2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e
- Candidate branch: release/phase-e-reviewed
- No push or deploy performed.

## Eight local commits

1. b4c70db frozen Phase-E offer handoff and score replay
2. 25c279d official mobile source and manufacturer-offer gates
3. 0c5be2f fresh exact manufacturer offers
4. 0421a19 manufacturer offers in API traces
5. ab94013 atomic retailer-offer persistence
6. 78553b1 Phase-G integration closure
7. eb73c95 semantic query-consistency release audit
8. b3b6539 exact-model query-signature correction

The source dependency path is the existing Python backend:
intent -> discovery -> canonical identity -> official evidence -> exact offer
freshness -> eligibility -> scoring/ranking -> API serialization. The GitHub Pages
surface uses the existing allow-listed artifact workflow and does not need the
Python backend files in its public artifact.

## Reviewed release files

- Existing source files from the eight commits.
- data/phase_e_release_evidence.json: one exact Vivo T5 Pro evidence record.
- data/retailer_product_registry.json: cw-mobile-96 Amazon ASIN plus Vivo SKU
  19410, kept as separate identifiers.
- test_phase_e_reviewed_t5_pro_release.py: four focused guards.
- reports/release_and_query_consistency/REVIEWED_STABLE_DATA_DIFF.md.

No current T5 Pro offer is released because the saved observation is expired.
The offer must be refreshed through the existing offer store before eligibility.

## Explicit exclusions

- data/retail_price_cache.json
- data/retailer_offers.json dirty additions, including cw-mobile-test
- data/verified_product_evidence_cache.json dirty runtime/research records
- runtime/discovery/audit JSON, outputs/, backups, phase_e_current.zip
- reports/master_system_audit/
- helper audit scripts

These remain in the owner's original worktree and were not staged.

## Clean-checkout validation

- Reviewed T5 evidence/identity/SKU/expiry tests: 4/4 PASS
- Focused integration set covering identity, manufacturer offers, release evidence,
  query consistency, API eligibility, score trace, frontend contract, premium guard
  and the reviewed T5 Pro package: 36/36 PASS
- Combined final focused run: 36 PASS / 1 FAIL across 37 tests.
- Offline harness portion: 5 PASS / 1 FAIL. The one failure is the preserved
  historical non-catalogue three-result fixture (FIXTURE_GAP); the approved
  two-result successor remains passing.
- Public Pages artifact exclusion test passed in the 32-test run.
- git diff --check: PASS.

## Runtime and deployment requirements

- python/shopping_api.py is the backend entry point; requirements.txt carries
  Gunicorn. No tracked render.yaml or Procfile defines the Render start command,
  so the dashboard command is still an external setting.
- data/retailer_offers.json and data/verified_product_evidence_cache.json are
  persistent mutable stores. Render persistent disk/database configuration is not
  present in this repository and is therefore UNVERIFIED/BLOCKED.
- No six-hour offer-refresh scheduler is present. Existing GitHub workflows are
  manual catalog validation, daily coupon updates, and manual Pages deployment;
  none refreshes mobile offers. Refresh ownership, cadence and alerting remain
  BLOCKED.
- Relevant runtime variable names are TAVILY_API_KEY, GEMINI_API_KEY,
  COUPONWORLD_LIVE_FAST and RENDER_GIT_COMMIT; no values are included.

## Readiness

- Backend source/data compatibility: PASS in clean checkout.
- Historical fixture: preserved FAIL/FIXTURE_GAP.
- GitHub Pages configuration: local workflow PASS; live run/artifact UNKNOWN.
- Render readiness: NO-GO until start command, persistent storage, refresh
  scheduler and deployed revision are verified.
- Production release: NO-GO.

## Authorized release sequence

1. Review this candidate commit and the stable-data diff.
2. Configure and verify Render start command, persistent storage and offer refresh.
3. Separately authorize push of the reviewed commits.
4. Run the existing manual Pages workflow and verify the artifact has no admin or
   internal files.
5. Verify live API, frontend, score explanations and refreshed T5 Pro offer.
6. Roll back to 2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e if any live gate fails.

