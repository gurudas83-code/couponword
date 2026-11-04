# Coupon World browser QA contract

This is a **release guard for the existing smartphone research experience**, not a new recommendation engine.

## What is checked

`scripts/browser_smoke.py` builds an HTTP server from the generated `public/` artifact and uses real Chromium at 390px, 768px and 1440px. It checks that research data is fetched, a strict budget query returns a research-only model, an exact 8GB/256GB query returns one documented Galaxy A36 identity, A36/A56 comparison displays a table without claiming a performance winner, and a visitor can opt in to handing the original query to the existing gated recommendation function. It also checks there are no active purchase CTAs on research results and no uncaught JavaScript exceptions.

## What is not certified

These checks do not verify retailer inventory or checkout, current prices, original manufacturer specifications, affiliate conversion, the Render backend implementation, or exhaustive mobile visual accessibility. A simulated callback is used to validate the handoff without bypassing or calling the live recommendation gates. The daily `research-quality.yml` workflow separately checks the real production homepage, generated catalogue, guide and Render `/health` endpoint.

## Local usage

```bash
python scripts/build_public_pages.py --output public
python -m pip install playwright==1.56.0
python -m playwright install chromium
python scripts/browser_smoke.py --root public --report browser-qa.json
```

The public Pages deployment workflow uses Ubuntu 24.04, installs the browser dependencies and runs this test before uploading or deploying. **A browser QA failure blocks a release.** Existing scoring, price-weight-zero rules, exact variant gates and preserved catalogues remain unchanged.
