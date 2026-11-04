# Coupon World release readiness snapshot — 2026-11-04

## Public-site improvements already merged
- Research queries can explicitly opt in to **full budget** coverage. Nearby band remains default, and every dated reference must still pass the evidence and exact-variant constraints.
- 13 research budget shortcuts, ₹10k–₹1L, are available.
- Camera, battery, gaming and other searches order research matches by the number of *relevant documented specifications* before broad spec coverage; this is **not a performance ranking**.
- An optional research-to-existing-recommendation-engine bridge is available on budget searches. The legacy/approved ranking and live-merchant eligibility gates are unchanged.
- Backend recommendation cards do not print price amounts; internal price and offer records remain intact for validation.
- Croma's general category link is clearly labelled as browsing, not an exact-model offer.

## Production safety / QA
- `.github/workflows/public-pages-artifact.yml` blocks a publish unless the exact generated public artifact builds, research/price/evidence contracts pass, server-side ranking and frontend regressions pass, and real Chromium tests pass at **390px, 768px and 1440px**.
- PR quality CI verified on run [41810091086](https://github.com/gurudas83-code/couponword/actions/runs/41810091086), **PASS**.
- Chromium browser CI verified on run [41810090751](https://github.com/gurudas83-code/couponword/actions/runs/41810090751), **PASS**.
- The first Pages attempt of the feature release [41809869189](https://github.com/gurudas83-code/couponword/actions/runs/41809869189) **failed closed** on two stale test fixtures; they were corrected via PR #10, without relaxing any production eligibility rule.
- These are GitHub Actions checks of generated local Pages artifacts. They do not certify all live production interactions or retailer availability.

## Available data, without exaggerated claims
- 232 smartphone research model cards; 235 discovery records; 10 frozen exact variants.
- 225 model cards with manufacturer-source-referenced specifications; 2,479 technical fields observed in the 2026-11-04 artifact audit.
- 86 dated **research price references**, not live prices or verified current offers.
- 696 retailer discovery/browse links; 232 generic Croma category destinations remain explicitly identified as such.
- 20 editorial buying guides. No new current, verified, in-stock merchant offer has been certified by these tasks.
- Price has **0% ranking weight**; a dated reference only determines a research budget gate.

## Separate Render backend deployment: external dependency
GitHub Actions read-only remote probe returned:
- `GET https://couponword.onrender.com/health` — PASS.
- Safe Galaxy A36/A56 research comparison — PASS (no purchase CTA).
- Runtime `revision`: `4e8ee0ba9f80a3090579ede1488df5288413383d`, dated 2026-10-29.
- That revision was already 21 source commits behind the GitHub Pages main branch at the time of audit, including changes to `python/shopping_api.py`. Updating GitHub Pages does **not** prove the Render app has redeployed.
- A maintainer with Render account permission must inspect the linked branch, auto-deploy settings, build/runtime status and deployment history, and redeploy the desired reviewed backend commit when safe. Do not claim updated engine behavior before verifying the Render `/health` revision.
- A Render integration is not connected in this chat; GitHub access alone does not authorize service deployment.

## Next data actions
Prioritize (a) exact India variants, (b) manufacturer verified specifications per field, (c) dated retailer observations with model/variant identity, (d) stock freshness and delivery evidence, (e) comparable independent performance measurements, before exposing eligible best-three or shopping CTAs. Do not create parallel ranking engines or back-fill invented prices.
