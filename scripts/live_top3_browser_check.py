#!/usr/bin/env python3
"""Read-only live Chromium audit of the deployed Top 3 research filter."""
from __future__ import annotations
import json
import time
from playwright.sync_api import sync_playwright

SITE = "https://coupon-world.in/"
SCENARIOS = [
    ("mobile", 390, 844, "top 3 phones under 25000"),
    ("desktop", 1365, 850, "top 3 battery phones"),
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
                }
                print("LIVE_TOP3_AUDIT " + json.dumps(output, ensure_ascii=False), flush=True)
                if cards.count() != 3: failures.append(device + " returned " + str(cards.count()) + " research selections")
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
