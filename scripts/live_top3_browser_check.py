#!/usr/bin/env python3
"""Read-only live Chromium audit of the deployed Top 3 research filter."""
from __future__ import annotations
import json
import time
from playwright.sync_api import sync_playwright

SITE = "https://coupon-world.in/"
SCENARIOS = [
    ("mobile-10k", 390, 844, "top 3 phones under 10000"),
    ("mobile-15k", 390, 844, "top 3 phones under 15000"),
    ("mobile-20k", 390, 844, "top 3 phones under 20000"),
    ("mobile-25k", 390, 844, "top 3 phones under 25000"),
    ("desktop-30k", 1365, 850, "top 3 phones under 30000"),
    ("desktop-battery", 1365, 850, "top 3 battery phones"),
    ("desktop-gaming", 1365, 850, "top 3 gaming phones"),
]

def main() -> None:
    failures = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for device, width, height, query in SCENARIOS:
            page = browser.new_page(viewport={"width": width, "height": height}, locale="en-IN")
            shopping_requests = []
            errors = []
            page.on("request", lambda request: shopping_requests.append(request.url) if "/api/recommend" in request.url else None)
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                response = page.goto(SITE, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_function("Boolean(window.CouponWorldMobileResearch)", timeout=45000)
                page.wait_for_function("""() => {
                    const label = document.getElementById("mobileResearchCatalogueCount");
                    return Boolean(label && label.textContent.includes("232 original catalogue models"));
                }""", timeout=45000)
                page.locator("#heroSearch").fill(query)
                started = time.perf_counter()
                page.locator("#heroSearchButton").click()
                page.wait_for_function("""() => {
                    const results = document.getElementById("mobileResearchResults");
                    return Boolean(results && results.innerText.includes("Research-Verified"));
                }""", timeout=12000)
                elapsed_ms = round((time.perf_counter() - started) * 1000)
                result = page.locator("#mobileResearchResults")
                cards = result.locator(".research-top3-result")
                titles = cards.locator("h3").all_text_contents()
                output = {
                    "device": device, "query": query, "http_status": response.status if response else None,
                    "visible_results": cards.count(), "names": titles, "time_after_data_loaded_ms": elapsed_ms,
                    "amazon_links": result.locator("a:has-text('Check live price on Amazon')").count(),
                    "flipkart_links": result.locator("a:has-text('Check live price on Flipkart')").count(),
                    "shopping_api_requests": shopping_requests, "page_errors": errors[:3],
                    "section_text": result.inner_text()[:600],
                    "reviewed_amounts": result.locator(".research-top3-result .research-source-note").all_text_contents(),
                    "unverified_budget_labels": result.inner_text().count("selected budget range unverified"),
                    "dated_price_band_labels": result.inner_text().count("Dated reference in selected band"),
                }
                print("LIVE_TOP3_AUDIT " + json.dumps(output, ensure_ascii=False), flush=True)
                expected_count = {
                    "mobile-10k": 1, "mobile-15k": 3, "mobile-20k": 3,
                    "mobile-25k": 3, "desktop-30k": 2,
                    "desktop-battery": 3, "desktop-gaming": 3,
                }[device]
                if cards.count() != expected_count:
                    failures.append(device + " returned " + str(cards.count()) +
                        " budget-qualified picks instead of " + str(expected_count))
                if "under " in query:
                    dated = result.inner_text().count("Dated reference in selected band; current price unverified")
                    if dated != cards.count():
                        failures.append(device + " showed ranked phone without dated price-band evidence")
                    if device == "mobile-10k":
                        if "lava bold n2 lite" not in result.inner_text().casefold() or "9,299" not in result.inner_text():
                            failures.append("₹10k is missing checked Lava Bold N2 Lite 3/64 ₹9,299")
                    if device == "mobile-15k":
                        for expected in ("Lava Bold N2", "Lava Virat V1", "10,499", "10,799", "12,999"):
                            if expected.casefold() not in result.inner_text().casefold():
                                failures.append("₹15k missing reviewed SKU evidence: " + expected)
                    if device in ("mobile-10k", "mobile-15k"):
                        if "OPPO A5x" in result.locator(".research-verified-top3").inner_text():
                            failures.append(device + " admitted mismatched OPPO A5x 4G/5G")
                        if result.locator("a:has-text('Dated price source')").count() != cards.count():
                            failures.append(device + " dated price source links missing")
                        if "Additional relevant phones" not in result.inner_text():
                            failures.append(device + " missing separately-labelled research alternatives")
                if len(titles) != len(set(titles)): failures.append(device + " duplicate model names")
                if result.locator("a:has-text('Check live price on Amazon')").count() != cards.count():
                    failures.append(device + " Amazon price-search links missing")
                if result.locator("a:has-text('Check live price on Flipkart')").count() != cards.count():
                    failures.append(device + " Flipkart price-search links missing")
                if shopping_requests: failures.append(device + " unexpectedly called live shopping API")
                if elapsed_ms > 1000: failures.append(device + " local search render exceeded 1s after catalogue ready")
                if errors: failures.append(device + " JavaScript exception: " + errors[0])
            except Exception as error:
                failures.append(device + ": " + str(error).split("\n")[0])
                print("LIVE_TOP3_AUDIT_ERROR " + device + ": " + repr(error), flush=True)
                try:
                    result = page.locator("#mobileResearchResults").inner_text(timeout=1000)
                    print("LIVE_TOP3_RESULT_TEXT " + json.dumps(result[:700], ensure_ascii=False), flush=True)
                except Exception:
                    pass
            finally:
                page.close()
        browser.close()
    if failures:
        raise SystemExit("LIVE_TOP3_FAILED: " + "; ".join(failures))
    print("LIVE_TOP3_PASS: production results and links checked in Chromium on mobile and desktop")

if __name__ == "__main__":
    main()
