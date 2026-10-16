# Coupon World — Complete Website Security Audit

**Audit date:** 2026-10-16 (Asia/Calcutta)
**Audit branch:** `security-audit-20261016`
**Audit base:** reviewed candidate `39eb9031a316f46d290e4b3c460c53c472e7be3e`
**Scope:** owned `coupon-world.in`, `couponword.onrender.com`, the Coupon World repository and its reviewed release artifact. Checks were bounded, read-only on live services and non-destructive locally. No secret value was copied into this report.

## A. Executive security verdict

The public Pages artifact is currently serving the intended public surface: known admin, validator, registry, evidence, offer, report, Python and ZIP paths returned 404 in bounded checks. The local allow-listed builder produced 110 files in 93 directories and no forbidden file or symlink was present in the checked repository.

Three reproducible source weaknesses were corrected only in this isolated audit branch: the Flask API no longer returns exception text to clients, frontend links reject non-HTTP(S) schemes and escape every generated URL attribute, and retailer price fetching rejects an unapproved HTTPS redirect destination before parsing it. Focused tests pass. These fixes are not deployed and are not in the reviewed release branch yet.

Remaining open risks are configuration and supply-chain issues: HTTP serves the homepage without an observed HTTPS redirect, the backend allows all CORS origins, workflow action references are floating and a scheduled coupon workflow has `contents: write`, and dependency advisories could not be verified because no local advisory tool or lockfile is present. No critical or high-confidence secret exposure was found.

**Overall security readiness:** CONDITIONAL
**MVP security release:** NO-GO until the local fixes are reviewed and deployed, CORS/transport decisions are made, and the Pages/Render smoke checks are repeated against the approved revision.

## B. Live exposure matrix

| URL or endpoint | Expected access | Observed access | Risk | Status |
|---|---|---|---|---|
| `https://coupon-world.in/` | Public homepage | HTTP 200 | None from bounded check | PASS |
| `http://coupon-world.in/` | Redirect to HTTPS | HTTP 200 without observed redirect | Clear-text access/configuration risk | OPEN |
| `https://coupon-world.in/admin.html` | Internal only | HTTP 404 | No current public shell | PASS |
| `https://coupon-world.in/validator.html` | Internal only | HTTP 404 | No current public validator | PASS |
| `/data/retailer_product_registry.json` | Internal | HTTP 404 | No current registry exposure | PASS |
| `/data/retailer_offers.json` | Internal | HTTP 404 | No current offer-store exposure | PASS |
| `/data/verified_product_evidence_cache.json` | Internal | HTTP 404 | No current evidence-cache exposure | PASS |
| `/reports/phase_e/final_certification.md` | Internal | HTTP 404 | No report exposure | PASS |
| `/phase_e_current.zip` | Internal | HTTP 404 | No archive exposure | PASS |
| `/.env` and `/python/shopping_api.py` | Internal | HTTP 404 | No known configuration/source exposure | PASS |
| `/app.js`, `/sitemap.xml`, `/coupons.json` | Public | HTTP 200 | Intended public assets | PASS |
| `https://couponword.onrender.com/health` | Public health check | HTTP 200, revision `2db6534...` | Live backend is old baseline | UNVERIFIED candidate parity |

The HTTP check used only known owned paths; no path brute force or third-party scan was performed.

## C. GitHub Pages security

The checked workflow is `.github/workflows/public-pages-artifact.yml`. It is `workflow_dispatch` only, has `contents: read`, `pages: write` and `id-token: write`, uses the existing Pages environment, builds through `scripts/build_public_pages.py`, verifies forbidden names, uploads the artifact and deploys with `actions/deploy-pages@v4`.

The local artifact inventory was:

```text
Top level: CNAME, app.js, assets, buying-guides.html, buying-guides.js,
coupons.json, data, index.html, products, robots.txt, seo, sitemap.xml, style.css
Files: 110    Directories: 93    Forbidden entries: 0
```

Only `data/seo-pages.json` is copied under `data/`; registry, offer, evidence, reports, Python, backups, outputs and ZIP files are excluded. The checked repository contains no symlinks. The builder does not explicitly reject a future symlink before `copytree`, so symlink rejection remains a low-confidence hardening recommendation if untrusted repository content will ever be published.

No pull-request trigger publishes Pages. The Pages workflow is manual, which avoids publishing unreviewed PR content. Action references are major tags rather than immutable commit SHAs. `bot.yml` is a separate scheduled workflow with `contents: write`; it modifies `coupons.json` and pushes to `main`. It does not directly deploy Pages, but it is a repository-integrity and supply-chain risk that should be reviewed before enabling automatic publishing.

## D. Backend and API security

The Flask application exposes two routes: `GET /health` and `GET /api/recommend`. No POST/PUT/PATCH/DELETE maintenance route was found. Query input is trimmed, empty input returns 400, and inputs longer than 300 characters return 400. The application runs with `debug=False`; Gunicorn is configured by the owner as `gunicorn --chdir python shopping_api:app --timeout 120`.

The API is intentionally public and therefore does not require authentication. The local route checks accepted budget, exact-model, RAM/storage, Unicode and special-character inputs without a server exception when the pipeline is isolated. No path or command input is accepted by the route. The health response exposes only service name, status and the `RENDER_GIT_COMMIT` revision.

The source originally returned `str(error)` in a 500 response. That reproduced information disclosure and is fixed locally by logging the exception server-side and returning only the generic error. The live service remains on the old SHA until a later approved deployment.

`CORS(app)` currently allows every origin. The local test confirmed an arbitrary `Origin: https://evil.example` receives an allow-origin response. The recommendation endpoint is public and read-only, so no private data access was demonstrated, but this increases browser-based abuse and resource-consumption exposure. Restricting CORS to the approved frontend and explicitly approved development origins is an owner/release decision.

No application security headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy` or `Permissions-Policy`) are configured in Flask, and the Pages response did not show HSTS. A CSP must be designed around the existing inline analytics and rendering scripts; it was not added speculatively.

## E. Repository and supply chain

The tracked-branch scan found no API-key pattern, GitHub token pattern, Render token, private-key block, `.env`, credential file or secret-like JSON file. The only filename containing “secret” is an ordinary public product slug. No secret rotation is indicated by this scan. This does not prove that an untracked local file or an external dashboard secret is safe.

`requirements.txt` pins Flask and Flask-Cors but uses open upper-bounded ranges for Gunicorn, Requests, BeautifulSoup, lxml, Pillow and Tavily. No Python lockfile, JavaScript package manifest or local `pip-audit`/equivalent advisory tool is present. Dependency vulnerability status is therefore **UNVERIFIED**, not PASS; no automatic upgrade was attempted.

GitHub Actions use `actions/checkout`, `setup-python`, Pages and upload/deploy actions by major tag. No malicious action or compromised revision was demonstrated, but immutable SHA pinning and a narrower write workflow are recommended before treating the repository as a hardened supply-chain boundary.

## F. Product and affiliate security

The existing product path preserves canonical product IDs, exact RAM/storage, manufacturer SKU and retailer ASIN separately. `retail_price_evidence.py` and `retailer_offer_store.py` enforce approved retailer/manufacturer hosts, positive prices, exact variants, availability and six-hour freshness. Expired and out-of-stock offers do not satisfy a budget query; Product DNA remains after offer expiry. Offer persistence is atomic and repeated admission is idempotent.

The public static coupon data currently contains 105 rows, all with HTTP(S) links; observed hosts were `www.amazon.in`, `amzn.to` and `amzn.in`. These links are intentionally public affiliate destinations, but the frontend previously inserted arbitrary link values through `safeLink()` without scheme validation. The audit branch now accepts only HTTP(S), blocks clear-text links on an HTTPS page and escapes every generated URL attribute.

Retailer price fetching followed redirects without checking the final destination. The audit branch now rechecks the final URL for an approved HTTPS host before parsing price data. The existing exact SKU, ASIN, source-host and freshness checks remain unchanged.

## G. Security findings register

| Finding | Severity | Evidence | Root cause | Fix/status | Verification |
|---|---|---|---|---|---|
| SEC-01 API exception disclosure | MEDIUM | Local forced pipeline exception returned `detail: INTERNAL_TEST_SENTINEL` | `shopping_api.py` serialized `str(error)` | Fixed locally; generic response plus server log | `test_security_audit.py` PASS |
| SEC-02 unsafe frontend URL scheme/raw attributes | MEDIUM | `safeLink()` returned arbitrary values and several `href`/`src` attributes were unescaped | Frontend trusted data before HTML insertion | Fixed locally with HTTP(S) validation and escaping | static security test and `node --check` PASS |
| SEC-03 redirect destination SSRF risk | MEDIUM | Allowed retailer URL could redirect to an unapproved host before parsing | Final `response.url` was not revalidated | Fixed locally; final HTTPS allow-list check | mocked redirect test PASS |
| SEC-04 wildcard CORS | MEDIUM | Local arbitrary origin received `Access-Control-Allow-Origin` | `CORS(app)` with no origin policy | Open configuration decision; no private route found | Local reproduction PASS |
| SEC-05 HTTP transport/HSTS gap | MEDIUM | `http://coupon-world.in/` returned 200; HTTPS response had no observed HSTS | Pages/custom-domain configuration | Owner/CDN action required | bounded live HTTP check |
| SEC-06 workflow write/supply-chain boundary | MEDIUM | `bot.yml` scheduled `contents: write`; actions are floating major tags | Broad automation permission and mutable action refs | Open review; no compromised action proven | workflow inspection |
| SEC-07 dependency advisories | LOW / UNVERIFIED | Ranged requirements, no lockfile or local advisory tool | Dependency reproducibility incomplete | Owner/developer dependency review | not independently verified |
| SEC-08 security headers | LOW | No application security-header middleware; CSP/HSTS absent from observed Pages headers | Header policy not defined | Recommend tested header policy; no speculative CSP | source/live header inspection |
| SEC-09 historical public internal files | CLOSED | Known internal URLs now return 404 | Legacy root artifact was replaced | Closed in current live check; keep regression test | live path matrix and local artifact test |

No critical issue or proven unauthorized administrative mutation was found. `admin.html` is excluded from the current public artifact and the live known URL is 404; the local page is a review-record generator without a network mutation route.

## H. Tests and evidence

| Check | Executed | Passed | Failed | Blocked / unverified |
|---|---:|---:|---:|---:|
| Focused security regression | 5 | 5 | 0 | 0 |
| JavaScript syntax check | 1 | 1 | 0 | 0 |
| Existing release-evidence regression | 7 | 7 | 0 | 0 |
| Existing manufacturer-offer regression | 4 | 4 | 0 | 0 |
| Existing atomic/idempotent offer store regression | 2 | 2 | 0 | 0 |
| Public artifact inventory | 110 files / 93 dirs | PASS | 0 | 0 |
| Local API validation and adversarial inputs | 8 bounded cases | PASS | 0 | 0 |
| Live Pages known-path checks | 14 URLs | PASS for expected 404/200 set | 0 | HTTP-to-HTTPS policy still open |
| Live Render health | 1 | HTTP 200 | 0 | candidate parity not verified |
| Dependency advisory scan | 0 | 0 | 0 | UNVERIFIED: no local tool/lockfile |

Existing Phase-E/Phase-G functional tests were not broadly rerun. The security patch reran only the affected release-evidence, manufacturer-offer and persistence tests. No live retailer, retailer-security or high-volume request was made.

## I. Exact local fixes

The isolated security branch contains these four file changes:

- `python/shopping_api.py` — stop returning exception detail to API clients;
- `app.js` — validate HTTP(S) URLs and HTML-escape generated URL attributes;
- `python/retail_price_evidence.py` — reject redirects outside approved HTTPS sources;
- `test_security_audit.py` — focused regression coverage for the three fixes, input limits and Pages artifact exclusion.

No ranking, scoring, identity, evidence, catalogue, workflow, Render or live data file was changed. The exact local security commit is produced after this report is reviewed and tested; it is not pushed or deployed.

## J. Owner actions

1. Review and separately approve the local security commit before merging it into `release/phase-e-reviewed`; do not cherry-pick it into production without the affected tests and frontend smoke.
2. Restrict backend CORS to `https://coupon-world.in` and explicitly approved development origins, then verify the frontend recommendation call.
3. Configure the custom domain/CDN to redirect HTTP to HTTPS and emit HSTS after confirming all public assets and affiliate links work over HTTPS.
4. Review `bot.yml`: remove unnecessary `contents: write`, require a reviewed/manual path, and pin third-party Actions to immutable SHAs before enabling repository writes.
5. Provide an approved dependency-audit path or lockfile review; do not auto-upgrade packages from this report.
6. After an approved deploy, verify `/health` revision, homepage, product page, recommendation API, affiliate navigation, score explanations and the known internal 404 paths.

No owner action is needed for secret rotation based on this bounded scan; rotate immediately if dashboard logs or any future scan reveal a real credential.

## K. Release safety

```text
SECURITY CRITICAL ISSUES: 0
SECURITY HIGH ISSUES: 0
SECURITY MEDIUM ISSUES: 6 open/conditional findings
SECURITY LOW ISSUES: 2
PUBLIC FILE EXPOSURE: PASS
SECRETS PROTECTION: PASS for tracked/public scan; dashboard secrets UNVERIFIED
API SECURITY: CONDITIONAL (local exception fix PASS; CORS restriction pending)
GITHUB ACTIONS SECURITY: CONDITIONAL
RENDER CONFIGURATION SECURITY: CONDITIONAL (health works; deployed revision is old)
DEPENDENCY SECURITY: UNVERIFIED
FRONTEND SECURITY: CONDITIONAL (local URL fix PASS; not deployed)
OVERALL SECURITY READINESS: CONDITIONAL
MVP SECURITY RELEASE: NO-GO
```

The proposed Free Render MVP is security-reviewable but not security-releasable until the three local fixes are reviewed, the CORS and HTTP transport decisions are resolved, and the approved candidate is deployed with live smoke evidence. No paid infrastructure, push, merge or deploy was performed.
