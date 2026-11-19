"""Exercise generated price UI, lazy loading and stale fallback in Chromium."""
import argparse
import copy
from datetime import datetime, timezone
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

def run(root):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(root.resolve())))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    payload = json.loads((root / "data/retailer_price_observations.json").read_text(encoding="utf-8"))
    # The committed API snapshot is intentionally historical. Test the fresh-price
    # UI branch using a browser-only synthetic timestamp, never retimestamp the
    # published JSON or falsely claim a live API refresh.
    fresh_fixture = copy.deepcopy(payload)
    fresh_at = datetime.now(timezone.utc).isoformat()
    for configurations in fresh_fixture["models"].values():
        for configuration in configurations:
            for offer in configuration["offers"]:
                offer["observed_at"] = fresh_at
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for width in (390, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    errors, requests = [], []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("request", lambda request: requests.append(request.url))
                    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
                    page.route("**/data/retailer_price_observations.json*", lambda route: route.fulfill(json=fresh_fixture))
                    page.route("**/api/recommend?*", lambda route: route.fulfill(json={"recommendations": []}, headers={"Access-Control-Allow-Origin": "*"}))
                    # Stub the private paid endpoint: browser QA must never spend credits.
                    page.route("**/api/price-observation?*", lambda route: route.fulfill(
                        json={"status": "no_exact_in_stock_observation", "attempts": []},
                        headers={"Access-Control-Allow-Origin": "*"}))
                    page.goto(url, wait_until="domcontentloaded")
                    page.wait_for_function("() => !!window.CouponWorldMobileResearch")
                    page.wait_for_function("() => window.CouponWorldMobileResearch.search('Galaxy A56').length > 0")
                    assert not any("retailer_price_observations" in request for request in requests)
                    page.locator("#heroSearch").fill("Samsung Galaxy A56 5G")
                    page.locator("#heroSearchButton").click()
                    button = page.locator('#mobileResearchResults [data-price-observations="samsung|galaxy a56 5g"]').first
                    button.click()
                    panel = button.locator("..").locator("[data-api-price-panel]")
                    panel.get_by_text("Price & availability observations", exact=True).wait_for()
                    # Opening saved observations must not automatically bill the API.
                    assert not any("/api/price-observation?" in request for request in requests)
                    assert panel.locator("[data-check-live-price]").count() == 1
                    assert panel.locator("tbody tr").count() > 0
                    assert panel.locator("img").count() == 0
                    priced_index = next(i for i, configuration in enumerate(payload["models"]["samsung|galaxy a56 5g"])
                                        if any(o.get("price") and o["availability"] == "in_stock" for o in configuration["offers"]))
                    panel.locator("[data-price-config]").select_option(index=priced_index)
                    panel.locator("[data-price-budget]").fill("1")
                    assert "Listed amount over your entered cap" in panel.inner_text()
                    assert any("retailer_price_observations" in request for request in requests)
                    select = panel.locator("[data-price-config]")
                    if select.locator("option").count() > 1:
                        select.select_option(index=1)
                    # Changing RAM/storage must also keep paid lookups opt-in.
                    assert not any("/api/price-observation?" in request for request in requests)
                    panel.locator("[data-check-live-price]").click()
                    panel.get_by_text("No exact in-stock listing was observed in the checked stores.").wait_for()
                    assert any("/api/price-observation?" in request for request in requests)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                    page.goto(url + "/tvs/india-20/tv01/", wait_until="domcontentloaded")
                    page.locator('[data-price-observations="TV01"]').click()
                    page.locator("[data-api-price-panel] table").wait_for()
                    assert "L55MC-IN" in page.locator("[data-api-price-panel]").inner_text()
                    page.close()
                    stale = browser.new_page(viewport={"width": width, "height": 900})
                    stale.route("https://www.googletagmanager.com/**", lambda route: route.abort())
                    for configurations in payload["models"].values():
                        for configuration in configurations:
                            for offer in configuration["offers"]:
                                offer["observed_at"] = "2020-01-01T00:00:00+00:00"
                    stale.route("**/data/retailer_price_observations.json*", lambda route: route.fulfill(json=payload))
                    stale.goto(url + "/tvs/india-20/tv01/", wait_until="domcontentloaded")
                    stale.locator('[data-price-observations="TV01"]').click()
                    stale.get_by_text("Previous stock observation; recheck retailer", exact=True).first.wait_for()
                    assert stale.locator(".api-observed-lowest").count() == 0
                    stale.close()
                    assert not errors, errors
                    print(f"PASS API prices {width}px: lazy load, mobile search, configurations, TV, no images, stale fallback")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("public"))
    run(parser.parse_args().root)
