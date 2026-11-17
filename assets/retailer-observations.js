(function () {
  "use strict";
  var snapshotPromise;
  var sequence = 0;
  var MAX_AGE_MS = 6 * 60 * 60 * 1000;
  function escape(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c];
    });
  }
  function fresh(offer) {
    var checked = Date.parse(offer.observed_at);
    return Number.isFinite(checked) && Date.now() >= checked && Date.now() - checked <= MAX_AGE_MS;
  }
  function safeUrl(offer) {
    try {
      var url = new URL(offer.product_url);
      if (url.protocol !== "https:" || url.username || url.password || url.port) return "";
      if (offer.retailer === "amazon" && url.hostname === "www.amazon.in" &&
          url.pathname === "/dp/" + offer.retailer_product_id && /^[A-Z0-9]{10}$/.test(offer.retailer_product_id)) return url.href;
      if (offer.retailer === "flipkart" && url.hostname === "www.flipkart.com" &&
          url.pathname.indexOf("/p/") >= 0 && url.searchParams.get("pid") === offer.retailer_product_id &&
          /^[A-Z0-9]{12,24}$/.test(offer.retailer_product_id)) return url.href;
      if (offer.retailer === "croma" && url.hostname === "www.croma.com" &&
          /^\d{5,9}$/.test(offer.retailer_product_id) &&
          new RegExp("/p/" + offer.retailer_product_id + "/?$").test(url.pathname)) return url.href;
    } catch (error) { /* Reject malformed source URLs. */ }
    return "";
  }
  function renderConfiguration(panel, configuration) {
    var offers = configuration.offers || [];
    var budgetInput = panel.querySelector("[data-price-budget]");
    var budget = budgetInput && budgetInput.value.trim() ? Number(budgetInput.value) : null;
    var eligible = offers.filter(function (offer) {
      return fresh(offer) && offer.availability === "in_stock" &&
        typeof offer.price === "number" && Number.isFinite(offer.price) && offer.price > 0 && safeUrl(offer);
    });
    var stores = new Set(eligible.map(function (offer) { return offer.retailer; }));
    var lowest = stores.size >= 2 ? Math.min.apply(null, eligible.map(function (offer) { return offer.price; })) : null;
    var rows = offers.map(function (offer) {
      var url = safeUrl(offer);
      if (!url) return "";
      var isFresh = fresh(offer);
      var status = !isFresh ? "Previous stock observation; recheck retailer" :
        offer.availability === "in_stock" ? "API observed in stock" :
        offer.availability === "out_of_stock" ? "API observed out of stock" : "Stock unknown";
      var price = typeof offer.price === "number" && Number.isFinite(offer.price) && offer.price > 0 ?
        "₹" + offer.price.toLocaleString("en-IN", {maximumFractionDigits: 2}) : "No payable price observed";
      var budgetNote = budget !== null && Number.isFinite(budget) && budget > 0 &&
        isFresh && typeof offer.price === "number" && offer.price > 0 ?
        "<small class=\"api-budget-check\">" + (offer.price <= budget ? "Listed amount within your entered cap" : "Listed amount over your entered cap") + "</small>" : "";
      var badge = lowest !== null && isFresh && offer.availability === "in_stock" && offer.price === lowest ?
        '<span class="api-observed-lowest">Lowest observed among these checked stores</span>' : "";
      var history = Array.isArray(offer.history) && offer.history.length > 1 ?
        "<details><summary>Recorded checks (" + offer.history.length + ")</summary><ul>" +
        offer.history.map(function (point) {
          var amount = typeof point.price === "number" && Number.isFinite(point.price) && point.price > 0 ?
            "₹" + point.price.toLocaleString("en-IN") : "No payable price observed";
          return "<li>" + escape(new Date(point.observed_at).toLocaleString("en-IN", {timeZone: "Asia/Kolkata"})) +
            " IST: " + escape(amount) + " · " + escape(point.availability) + "</li>";
        }).join("") + "</ul></details>" : "";
      var rel = "noopener noreferrer nofollow" + (offer.retailer === "amazon" && new URL(url).searchParams.has("tag") ? " sponsored" : "");
      return "<tr><th scope=\"row\">" + escape(offer.retailer) + "</th><td>" + escape(price) + badge + budgetNote +
        "</td><td>" + escape(status) + "</td><td><time datetime=\"" + escape(offer.observed_at) + "\">" +
        escape(new Date(offer.observed_at).toLocaleString("en-IN", {timeZone: "Asia/Kolkata"})) +
        " IST</time>" + history + "</td><td><a href=\"" + escape(url) + "\" target=\"_blank\" rel=\"" + rel + "\">Check retailer</a></td></tr>";
    }).join("");
    panel.querySelector("[data-price-table]").innerHTML = '<p><strong>Listed configuration:</strong> ' +
      escape(configuration.variant) + " · Pincode " + escape(configuration.pincode) +
      '</p><div class="api-observation-scroll"><table><caption>Saved price and stock observations (QuickCommerce source)</caption>' +
      '<thead><tr><th scope="col">Store</th><th scope="col">Listed price</th><th scope="col">Stock observation</th><th scope="col">Checked</th><th scope="col">Retailer</th></tr></thead><tbody>' +
      rows + "</tbody></table></div>" +
      (stores.size < 2 ? "<p>No same-configuration comparison across two fresh in-stock stores is available.</p>" : "");
  }
  function show(panel, payload, modelKey) {
    var configurations = (payload.models || {})[modelKey] || [];
    panel._priceConfigurations = configurations;
    if (!configurations.length) {
      panel.innerHTML = '<p role="status">No matching API price observation for this catalogue entry. This does not mean unavailable. Use the retailer links to check.</p>';
      return;
    }
    var id = "api-price-config-" + (++sequence);
    panel.innerHTML = '<h4>Price &amp; availability observations</h4><p>Source: previously saved QuickCommerce third-party observations. Opening this panel does not call the paid API. Prices are not checkout confirmation.</p>' +
      '<label for="' + id + '">Choose the listed configuration</label><select id="' + id + '" data-price-config>' +
      configurations.map(function (configuration, index) {
        return '<option value="' + index + '">' + escape(configuration.variant) + "</option>";
      }).join("") + '</select><label>Check this configuration against your budget (₹)<input type="number" min="1" step="1" inputmode="numeric" data-price-budget placeholder="Optional price cap"></label><div data-price-table></div>' +
      '<p class="api-observation-note">Prices can change. Bank/exchange offers and delivery charges are excluded. Confirm India variant, seller condition, warranty and delivery with the retailer. Manufacturer specifications remain separately sourced. Price has 0% weight in product quality ranking.</p>';
    renderConfiguration(panel, configurations[0]);
    panel.querySelector("[data-price-config]").addEventListener("change", function (event) {
      renderConfiguration(panel, configurations[Number(event.target.value)]);
    });
    panel.querySelector("[data-price-budget]").addEventListener("input", function () {
      renderConfiguration(panel, configurations[Number(panel.querySelector("[data-price-config]").value)]);
    });
  }
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-price-observations]");
    if (!button) return;
    var parent = button.closest(".api-price-observations");
    var panel = parent.querySelector("[data-api-price-panel]");
    var open = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(open));
    panel.hidden = !open;
    if (!open) return;
    if (panel.dataset.loaded === "true") {
      var selected = panel.querySelector("[data-price-config]");
      if (selected && panel._priceConfigurations) renderConfiguration(panel, panel._priceConfigurations[Number(selected.value)]);
      return;
    }
    panel.innerHTML = '<p role="status">Loading saved price checks…</p>';
    if (!snapshotPromise) {
      snapshotPromise = fetch("/data/retailer_price_observations.json?v=20261117", {credentials: "omit"}).then(function (response) {
        if (!response.ok) throw new Error("Observation file unavailable");
        return response.json();
      }).then(function (payload) {
        if (payload.mode !== "ATTRIBUTED_API_PRICE_OBSERVATIONS") throw new Error("Unexpected observation data");
        return payload;
      }).catch(function (error) { snapshotPromise = null; throw error; });
    }
    snapshotPromise.then(function (payload) {
      if (!panel.isConnected) return;
      show(panel, payload, button.getAttribute("data-price-observations"));
      panel.dataset.loaded = "true";
    }).catch(function () {
      panel.innerHTML = '<p role="status">Saved observations are temporarily unavailable. Check the retailer directly.</p>';
    });
  });
}());
