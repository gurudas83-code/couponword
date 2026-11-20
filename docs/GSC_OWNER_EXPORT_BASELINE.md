# Google Search Console owner-export indexing and traffic baseline

## Scope

The published site has passed a technical sitemap indexability check (199/199
on 20 November 2026). **This is NOT Google's indexed-page count.**
GSC clicks, impressions and indexed counts must come from the owner's real
Search Console exports, not a technical crawl or public search engine.

The scripts/gsc_owner_export_audit.py tool runs read-only, offline and without
Google credentials or live APIs. It changes neither production nor the sitemap.

## Get the evidence from the same Search Console property

1. Open https://search.google.com/search-console and select the existing
   coupon-world.in domain property (sc-domain:coupon-world.in), or
   https://coupon-world.in/ URL-prefix property. Keep this unchanged for both
   exports. These property types can cover different URLs.
2. **Performance > Search results**: use Web, Last 28 days, no query/page/
   country/device filters; Export > Download CSV. Retain the original ZIP,
   including the dated chart and page/query tables.
3. **Indexing > Pages**: select All known pages and Export > Download CSV.
   Retain the ZIP containing an indexed/not-indexed chart and a reasons table.
   Record if you use another scope such as All submitted pages.
4. Keep ZIPs private: do not commit site search terms or traffic data to
   the public GitHub repository.

Official export guidance:
https://support.google.com/webmasters/answer/12919797
https://support.google.com/webmasters/answer/7576553
https://support.google.com/webmasters/answer/7440203

## Offline commands

Run from repository root (replace the file paths with actual downloads):

    python scripts/build_public_pages.py --output public
    python -m unittest -q test_gsc_owner_exports
    python -m scripts.gsc_owner_export_audit \
      --sitemap public/sitemap.xml \
      --performance-zip /private/GSC_Performance.zip \
      --indexing-zip /private/GSC_Page_Indexing.zip \
      --property sc-domain:coupon-world.in \
      --output-dir /private/coupon-world-gsc-report

For URL-prefix property use the --property value https://coupon-world.in/.
Either ZIP can be omitted, but at least one genuine owner export is required.
ZIP filenames may vary; the parser identifies tables by CSV column headers.

## Output

- baseline.json: Property-wide chart-derived total clicks/impressions for the
  selected date range; latest indexed/not-indexed chart counts where available;
  reason counts; evidence warnings and user-declared property.
- candidate-sitemap-performance.csv: current sitemap candidate URLs and any
  visible corresponding Performance page rows. No per-URL indexing verdict is
  asserted. Absence from the page table does NOT prove not-indexed status.
- query-evidence.csv: actual query, clicks, impressions, CTR and position
  evidence for editorial prioritization, not predicted ranking or traffic.

## Crucial safeguards

- CSV ZIPs have no authenticated Search Console property identity. The
  --property value is a declaration, not verified proof of the ZIP's origin.
- Property-wide Page Indexing counts are NOT the number of the live 199 URLs
  that Google has indexed. A full URL Inspection or corresponding GSC URL
  evidence is needed for a per-sitemap-URL indexing verdict.
- Anonymized queries and grouping rules can cause page/query table totals
  to differ from the property-wide chart. The analyzer never adds page or
  query rows and calls the result overall traffic.
- Missing chart inputs produce null counts, never fabricated zero metrics.
- Technical eligibility, sitemap inclusion, and an HTTP 200 response are
  not guarantees that Google indexed the page.
- This workflow deliberately does not request Google account credentials,
  modify public pages or make any paid API calls.

## After real exports

Review GSC-reported discover/crawl-not-indexed reasons, actual high-impression
low-CTR queries, and the Top 30 pages with evidence. Make only supported
content changes and run CI before deployment.
