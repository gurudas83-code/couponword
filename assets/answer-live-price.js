(function () {
  "use strict";
  var endpoint = "https://couponword.onrender.com/api/price-observation";

  function escape(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return {"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c];
    });
  }

  function money(value) {
    return typeof value === "number" && Number.isFinite(value) && value > 0
      ? "₹" + value.toLocaleString("en-IN") : "Price not returned";
  }

  function checked(value) {
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? "time unavailable" :
      date.toLocaleString("en-IN", {timeZone:"Asia/Kolkata"}) + " IST";
  }

  function retailerUrl(offer) {
    try {
      var url = new URL(offer.product_url || "");
      if (url.protocol !== "https:" || url.username || url.password || url.port) return "";
      if (offer.retailer === "amazon" && url.hostname === "www.amazon.in" &&
          /^\/dp\/[A-Z0-9]{10}$/.test(url.pathname)) return url.href;
      if (offer.retailer === "flipkart" && url.hostname === "www.flipkart.com" &&
          url.pathname.indexOf("/p/") >= 0 && url.searchParams.get("pid")) return url.href;
      if (offer.retailer === "croma" && url.hostname === "www.croma.com") return url.href;
    } catch (error) { /* Keep malformed provider URLs out of the page. */ }
    return "";
  }

  function render(result, payload) {
    if (payload.status === "budget_exhausted") {
      result.innerHTML = "<p><strong>Live price check paused for today.</strong> The paid observation budget is exhausted. No stale price is being shown as current; please try again after the next reset.</p>";
      return;
    }
    if (payload.status === "not_configured" || payload.status === "provider_unavailable") {
      result.innerHTML = "<p>Live retailer connector is temporarily unavailable. Current price is intentionally withheld.</p>";
      return;
    }
    if (payload.status !== "ok" || !payload.configuration) {
      result.innerHTML = "<p>No exact in-stock observation was returned for this RAM/storage variant. This does not prove that the phone is unavailable.</p>";
      return;
    }
    var cfg = payload.configuration;
    var rows = (cfg.offers || []).map(function (offer) {
      var url = retailerUrl(offer);
      return "<tr><th scope=\"row\">" + escape(offer.retailer) + "</th><td>" + money(offer.price) +
        "</td><td>" + escape(offer.availability || "unknown") + "</td><td>" + checked(offer.observed_at) +
        "</td><td>" + (url ? "<a href=\"" + escape(url) + "\" target=\"_blank\" rel=\"nofollow sponsored noopener noreferrer\">Check retailer</a>" : "Not available") + "</td></tr>";
    }).join("");
    result.innerHTML = "<p><strong>Exact configuration:</strong> " + escape(cfg.variant || "requested RAM/storage") +
      " · Pincode " + escape(payload.pincode || "110001") + "</p><div class=\"live-price-scroll\"><table><caption>Paid API observation (not checkout confirmation)</caption><thead><tr><th>Retailer</th><th>Price</th><th>Stock</th><th>Checked</th><th>Link</th></tr></thead><tbody>" + rows +
      "</tbody></table></div><p class=\"live-price-disclaimer\">Prices, seller, delivery and bank/exchange offers can change. Confirm the final payable amount on the retailer page.</p>";
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-live-price-check]");
    if (!button || button.dataset.loading === "true") return;
    var card = button.closest(".answer-live-price");
    var result = card && card.querySelector("[data-live-price-result]");
    if (!result) return;
    var params = new URLSearchParams({model_key: button.getAttribute("data-live-price-check") || ""});
    var ram = button.getAttribute("data-live-price-ram");
    var storage = button.getAttribute("data-live-price-storage");
    if (ram) params.set("ram_gb", ram);
    if (storage) params.set("storage_gb", storage);
    button.dataset.loading = "true";
    button.disabled = true;
    result.textContent = "Checking the exact variant…";
    fetch(endpoint + "?" + params.toString(), {credentials:"omit"})
      .then(function (response) { return response.json().then(function (payload) { return {ok:response.ok, payload:payload}; }); })
      .then(function (response) { render(result, response.payload || {}); })
      .catch(function () { result.innerHTML = "<p>Live price service could not be reached. Current price is intentionally withheld.</p>"; })
      .finally(function () { button.dataset.loading = "false"; button.disabled = false; });
  });
}());
