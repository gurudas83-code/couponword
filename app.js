const DEALS_FILE = "/coupons.json?v=" + Date.now();

let allDeals = [];
let activeCategory = "All";
let activeView = "grid";

const grid = document.getElementById("dealsGrid");
const searchInput = document.getElementById("searchInput");
const heroSearch = document.getElementById("heroSearch");
const heroSearchButton = document.getElementById("heroSearchButton");
const sortSelect = document.getElementById("sortSelect");
const chipsBox = document.getElementById("categoryChips");
const resultsCount = document.getElementById("resultsCount");

async function loadDeals() {
  try {
    const res = await fetch(DEALS_FILE);
    if (!res.ok) throw new Error("coupons.json not found");

    allDeals = await res.json();

    updateStats();
    buildCategoryChips();
    renderFeaturedDeal();
    renderDeals();
  } catch (err) {
    grid.innerHTML = `<div class="state-card"><strong>Unable to load deals</strong><span>Check coupons.json file.</span></div>`;
    resultsCount.textContent = "No deals loaded";
  }
}

function normalize(text) {
  return String(text || "").toLowerCase().trim();
}

function getSearchText(deal) {
  return [
    deal.title,
    deal.store,
    deal.category,
    deal.discount,
    deal.code,
    deal.price,
    deal.mrp,
    deal.save,
    deal.expiry
  ].join(" ");
}

function extractNumber(value) {
  const match = String(value || "").match(/\d+/);
  return match ? Number(match[0]) : 0;
}

function getFilteredDeals() {
  const query = normalize(searchInput.value);

  let deals = allDeals.filter(deal => {
    const matchSearch = normalize(getSearchText(deal)).includes(query);
    const matchCategory =
      activeCategory === "All" ||
      normalize(deal.category) === normalize(activeCategory);

    return matchSearch && matchCategory;
  });

  if (sortSelect.value === "latest") {
    deals.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
  }

  if (sortSelect.value === "discount") {
    deals.sort((a, b) => extractNumber(b.discount) - extractNumber(a.discount));
  }

  if (sortSelect.value === "az") {
    deals.sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
  }

  return deals;
}

function updateStats() {
  document.getElementById("statDeals").textContent = allDeals.length;

  const categories = new Set(allDeals.map(d => d.category).filter(Boolean));
  document.getElementById("statCategories").textContent = categories.size;
}

function buildCategoryChips() {
  const categories = ["All", ...new Set(allDeals.map(d => d.category).filter(Boolean))];

  chipsBox.innerHTML = categories.map(cat => `
    <button type="button" class="chip ${cat === activeCategory ? "active" : ""}" data-category="${escapeHTML(cat)}">
      ${escapeHTML(cat)}
    </button>
  `).join("");

  chipsBox.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
      activeCategory = btn.dataset.category;
      buildCategoryChips();
      renderDeals();
    });
  });
}

function renderFeaturedDeal() {
  const box = document.getElementById("featuredDeal");
  const deal = allDeals[0];

  if (!deal) return;

  box.innerHTML = `
    ${renderImage(deal, "spotlight-image")}
    <h2>${escapeHTML(deal.title || "Hot Deal")}</h2>
    <p>${escapeHTML(deal.discount || "Latest offer")} • ${escapeHTML(deal.category || "Deal")}</p>
    <a href="${safeLink(deal.link)}" target="_blank" rel="nofollow sponsored noopener">View Deal</a>
  `;
}

function renderDeals() {
  const deals = getFilteredDeals();

  resultsCount.textContent = `${deals.length} deal${deals.length !== 1 ? "s" : ""} found`;

  if (!deals.length) {
    grid.innerHTML = `<div class="state-card"><strong>No matching deals found</strong><span>Try another keyword or category.</span></div>`;
    return;
  }

  grid.className = activeView === "compact" ? "deal-grid compact" : "deal-grid";

  grid.innerHTML = deals.map(deal => `
    <article class="deal-card">
      ${renderImage(deal, "deal-image")}

      <div class="deal-meta">
        <span class="store">${escapeHTML(deal.store || "Online Store")}</span>
        <span class="category-pill">${escapeHTML(deal.category || "Deal")}</span>
      </div>

      <h3 class="deal-title">${escapeHTML(deal.title || "Amazon Product Deal")}</h3>

      <div class="discount">${escapeHTML(deal.discount || "Deal Price")}</div>

      <div class="price-row">
        ${deal.price ? `<span class="price">${escapeHTML(deal.price)}</span>` : ""}
        ${deal.mrp ? `<span class="mrp">${escapeHTML(deal.mrp)}</span>` : ""}
        ${deal.save ? `<span class="save">${escapeHTML(deal.save)}</span>` : ""}
      </div>

      <p class="description">${escapeHTML(deal.description || "Check the latest price, availability and offer on the retailer site before buying.")}</p>

      <div class="code-row">
        <span>${escapeHTML(deal.code || "NO CODE NEEDED")}</span>
        <span>${escapeHTML(deal.expiry || "Limited Time")}</span>
      </div>

      <a class="shop-button" href="${safeLink(deal.link)}" target="_blank" rel="nofollow sponsored noopener">
        Get Deal →
      </a>

      <div class="card-note">Price and availability may change on the retailer site</div>
    </article>
  `).join("");
}

function categoryPlaceholder(category) {
  const key = String(category || "").toLowerCase().trim();

  const placeholders = {
    "mobiles": "mobiles.svg",
    "mobile": "mobiles.svg",
    "smartphones": "mobiles.svg",
    "cell phones & accessories": "mobiles.svg",
    "electronics": "electronics.svg",
    "laptops": "laptops.svg",
    "computers": "laptops.svg",
    "audio": "audio.svg",
    "headphones": "audio.svg",
    "speakers": "audio.svg",
    "fashion": "fashion.svg",
    "clothing": "fashion.svg",
    "footwear": "fashion.svg",
    "home": "home-kitchen.svg",
    "home & kitchen": "home-kitchen.svg",
    "home improvement": "home-kitchen.svg",
    "beauty": "beauty.svg",
    "health & personal care": "beauty.svg",
    "grocery": "grocery.svg",
    "appliances": "appliances.svg"
  };

  return `assets/images/categories/${placeholders[key] || "default.svg"}`;
}

function renderImage(deal, className) {
  const fallbackImage = categoryPlaceholder(deal.category);
  const displayImage = deal.image || fallbackImage;

  return `
    <div class="${className}">
      <img
        src="${escapeHTML(displayImage)}"
        alt="${escapeHTML(deal.title || "Deal image")}"
        loading="lazy"
        decoding="async"
        onerror="this.onerror=null;this.src='${escapeHTML(fallbackImage)}'">
    </div>
  `;
}

function applySearch(value) {
  searchInput.value = value || "";
  document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
  renderDeals();
}

function safeLink(link) {
  return link || "#";
}

function trackAnalyticsEvent(eventName, params = {}) {
  try {
    if (typeof window.gtag === "function") {
      window.gtag("event", eventName, params);
    }
  } catch (error) {
    console.warn("Coupon World analytics event failed:", eventName, error);
  }
}

function analyticsSearchTerm(value) {
  return String(value || "")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[email]")
    .replace(/(?:\+?91[\s-]?)?[6-9]\d{9}/g, "[phone]")
    .trim()
    .slice(0, 100);
}

function retailerFromLink(link) {
  try {
    return new URL(link.href, window.location.href).hostname
      .replace(/^www\./, "")
      .slice(0, 100);
  } catch (error) {
    return "unknown";
  }
}

document.addEventListener("click", event => {
  const link = event.target.closest('a[rel~="sponsored"]');

  if (!link || link.dataset.aiRetailerClick === "1") {
    return;
  }

  const card = link.closest(".deal-card, #featuredDeal");
  const title = card
    ? card.querySelector(".deal-title, h2, h3")?.textContent
    : "";

  trackAnalyticsEvent("affiliate_click", {
    retailer: retailerFromLink(link),
    link_placement: link.closest("#featuredDeal")
      ? "featured_deal"
      : "deal_card",
    product_title: String(title || "").trim().slice(0, 100)
  });
});

function escapeHTML(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

searchInput.addEventListener("input", renderDeals);
sortSelect.addEventListener("change", renderDeals);

heroSearchButton.addEventListener("click", () => {
  const query = heroSearch.value;
  applySearch(query);
  loadShoppingRecommendation(query);
});

heroSearch.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    const query = heroSearch.value;
    applySearch(query);
    loadShoppingRecommendation(query);
  }
});

document.querySelectorAll("[data-search]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.search));
});

document.querySelectorAll("[data-quick]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.quick));
});

document.querySelectorAll("[data-view]").forEach(btn => {
  btn.addEventListener("click", () => {
    activeView = btn.dataset.view;

    document.querySelectorAll("[data-view]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    renderDeals();
  });
});

loadDeals();
// Hide unverified discount labels from all product cards.
function removeUnverifiedDiscounts() {
  const discountPattern = /^\s*\d+(?:\.\d+)?\s*%\s*OFF\s*$/i;

  document
    .querySelectorAll(
      ".discount, .discount-badge, .discount-text, .product-discount, .deal-discount, [data-discount]"
    )
    .forEach((element) => element.remove());

  document.querySelectorAll("body *").forEach((element) => {
    const hasChildElements = element.children.length > 0;
    const text = element.textContent?.trim() || "";

    if (!hasChildElements && discountPattern.test(text)) {
      element.remove();
    }
  });
}

document.addEventListener("DOMContentLoaded", removeUnverifiedDiscounts);

// Also run after dynamically rendered products.
setTimeout(removeUnverifiedDiscounts, 300);
async function loadShoppingRecommendation(query) {
  const card = document.getElementById("shoppingBrainCard");
  const section = document.getElementById("aiRecommendation");

  if (!card) {
    console.error("shoppingBrainCard element not found");
    return;
  }

  const cleanQuery = String(query || "").trim();
  const analyticsQuery = analyticsSearchTerm(cleanQuery);

  if (!cleanQuery) {
    card.innerHTML = `
      <h3>Ask Coupon World</h3>
      <p>Search for a product above to get personalized AI recommendations.</p>
    `;
    return;
  }

  trackAnalyticsEvent("ai_search_submit", {
    search_term: analyticsQuery
  });

  card.innerHTML = `
    <h3>Finding the best matches...</h3>
    <p>Coupon World AI is checking products, prices and fit for your request.</p>
  `;

  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  try {
    const endpoint =
      "https://couponword.onrender.com/api/recommend?q=" +
      encodeURIComponent(cleanQuery);

    const response = await fetch(endpoint);

    if (!response.ok) {
      throw new Error(`Shopping API returned HTTP ${response.status}`);
    }

    const data = await response.json();

    console.log("Shopping Brain live response:", data);

    const recommendations = Array.isArray(data.recommendations)
      ? data.recommendations
      : [];

    const exactModelQuery =
      Boolean(data.exact_model_scope) &&
      data.exact_model_scope.active === true;

    const recommendationPass =
      String(data.result_status || "").toUpperCase() === "PASS";

    const rawTotalSeconds =
      data.timings && data.timings.total_seconds;

    const totalSeconds =
      rawTotalSeconds != null &&
      rawTotalSeconds !== "" &&
      Number.isFinite(Number(rawTotalSeconds))
        ? Number(rawTotalSeconds)
        : null;

    const resultAnalytics = {
      search_term: analyticsQuery,
      result_status: String(data.result_status || ""),
      response_status: String(data.status || ""),
      recommendation_count: recommendations.length,
      exact_model_query: exactModelQuery ? 1 : 0,
      exact_model_success:
        exactModelQuery && recommendationPass &&
        recommendations.length > 0 ? 1 : 0,
      recommendation_pass: recommendationPass ? 1 : 0,
      zero_result: recommendations.length === 0 ? 1 : 0
    };

    if (Number.isFinite(totalSeconds)) {
      resultAnalytics.total_seconds = totalSeconds;
      resultAnalytics.api_latency_ms = Math.round(totalSeconds * 1000);
    }

    trackAnalyticsEvent("ai_search_result", resultAnalytics);

    if (recommendations.length > 0) {
      const topRecommendation = recommendations[0] || {};
      const topOffers = Array.isArray(topRecommendation.retailer_offers)
        ? topRecommendation.retailer_offers
        : [];

      const topBestOffer =
        topRecommendation.best_offer &&
        typeof topRecommendation.best_offer === "object"
          ? topRecommendation.best_offer
          : null;

      const topOffer = topBestOffer || topOffers[0] || {};
      const rawTopFit = topRecommendation.fit_percent;
      const topFit =
        rawTopFit != null &&
        rawTopFit !== "" &&
        Number.isFinite(Number(rawTopFit))
          ? Number(rawTopFit)
          : null;

      const viewAnalytics = {
        search_term: analyticsQuery,
        recommendation_count: recommendations.length,
        top_product_id: String(
          topOffer.product_id ||
          topRecommendation.product_id ||
          ""
        ),
        top_rank: Number(topRecommendation.rank || 1)
      };

      if (Number.isFinite(topFit)) {
        viewAnalytics.top_fit_percent = topFit;
      }

      trackAnalyticsEvent("recommendation_view", viewAnalytics);
    }

    if (recommendations.length === 0) {
      trackAnalyticsEvent("zero_result", {
        search_term: analyticsQuery,
        result_status: String(data.result_status || ""),
        exact_model_query: exactModelQuery ? 1 : 0
      });

      card.innerHTML = `
        <h3>No strong match found</h3>
        <p>Try changing the budget, RAM, storage, brand or other requirements.</p>
      `;
      return;
    }

    card.innerHTML = recommendations.map((p) => {
      const title = escapeHTML(p.title || "Recommended Product");
      const brand = escapeHTML(p.brand || "Not available");
      const fitNumber =
        p.fit_percent != null &&
        p.fit_percent !== "" &&
        Number.isFinite(Number(p.fit_percent))
          ? Math.max(0, Math.min(100, Number(p.fit_percent)))
          : null;

      const fitDisplay =
        fitNumber != null ? `${fitNumber}%` : "Not available";

      const evidenceNumber =
        p.evidence_coverage_percent != null &&
        p.evidence_coverage_percent !== "" &&
        Number.isFinite(Number(p.evidence_coverage_percent))
          ? Math.max(0, Math.min(100, Number(p.evidence_coverage_percent)))
          : null;

      const evidenceDisplay =
        evidenceNumber != null ? `${evidenceNumber}%` : "Not available";

      const confidence = escapeHTML(p.confidence || "unknown");

      const offers = Array.isArray(p.retailer_offers)
        ? p.retailer_offers
        : [];

      // Respect the backend comparison contract:
      // best_offer exists only when enough trustworthy comparable
      // retailer offers are available. A single verified offer is
      // still useful, but must not be presented as "best".
      const bestOffer =
        p.best_offer && typeof p.best_offer === "object"
          ? p.best_offer
          : null;

      const primaryOffer = bestOffer || offers[0] || {};

      const variant = primaryOffer.variant
        ? escapeHTML(primaryOffer.variant)
        : "Not available";

      const retailer = primaryOffer.retailer
        ? escapeHTML(primaryOffer.retailer)
        : "Not available";

      const retailerHeading = bestOffer
        ? "Best verified retailer"
        : offers.length > 0
          ? "Verified retailer"
          : "Retailer";

      const lastChecked = primaryOffer.last_checked
        ? escapeHTML(primaryOffer.last_checked)
        : "Not available";

      const priceEvidence =
        p.provenance && p.provenance.price_evidence
          ? p.provenance.price_evidence
          : {};

      const retailerAvailability = String(
        primaryOffer.availability || ""
      ).trim().toLowerCase();

      let priceStatusRaw;

      if (offers.length > 0) {
        if (
          primaryOffer.price != null &&
          primaryOffer.price !== ""
        ) {
          priceStatusRaw =
            retailerAvailability &&
            retailerAvailability !== "unknown"
              ? `price available ? ${retailerAvailability.replaceAll("_", " ")}`
              : "price available ? availability not verified";
        } else {
          priceStatusRaw = "price unavailable";
        }
      } else {
        priceStatusRaw =
          priceEvidence.status ||
          (p.price != null ? "available" : "unavailable");
      }

      const priceStatus = escapeHTML(
        String(priceStatusRaw).replaceAll("_", " ")
      );

      const priceStatusHeading =
        offers.length > 0
          ? "Retailer offer status"
          : "Price status";

      const imageUrl = safeLink(p.image_url);

      const selectedPrice =
        primaryOffer.price != null &&
        primaryOffer.price !== ""
          ? primaryOffer.price
          : p.price;

      const price =
        selectedPrice != null &&
        selectedPrice !== ""
          ? `\u20B9${escapeHTML(selectedPrice)}`
          : "Check latest price";

      // retailer_offers and best_offer are sanitized by the backend.
      // Prefer that exact retailer URL so displayed retailer, price
      // and CTA all refer to the same offer.
      const productLink = safeLink(
        primaryOffer.product_url ||
        p.market_source ||
        p.official_source ||
        p.link
      );

      const offerCtaLabel = bestOffer
        ? "View Best Verified Offer \u2192"
        : offers.length > 0
          ? "Check Verified Retailer \u2192"
          : "Check Price \u2192";

      const why = Array.isArray(p.why_it_fits)
        ? p.why_it_fits
        : [];

      const whyHTML = why.length
        ? `
          <div class="ai-detail-block ai-positive">
            <div class="ai-detail-title">Why it fits</div>
            <ul class="ai-reasons">
              ${why.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      const tradeoffs = Array.isArray(p.tradeoffs)
        ? p.tradeoffs
        : [];

      const tradeoffsHTML = tradeoffs.length
        ? `
          <div class="ai-detail-block ai-tradeoffs">
            <div class="ai-detail-title">Trade-offs</div>
            <ul>
              ${tradeoffs.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      const unknowns = Array.isArray(p.unknown)
        ? p.unknown
        : [];

      const unknownsHTML = unknowns.length
        ? `
          <div class="ai-detail-block ai-unknowns">
            <div class="ai-detail-title">Missing / uncertain evidence</div>
            <ul>
              ${unknowns.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      return `
        <article class="ai-result-card">
          <div class="ai-result-rank">#${escapeHTML(p.rank || "")}</div>

          ${
            imageUrl !== "#"
              ? `
                <div class="ai-result-image-wrap">
                  <img
                    class="ai-result-image"
                    src="${imageUrl}"
                    alt="${title}"
                    loading="lazy"
                  />
                </div>
              `
              : ""
          }

          <h3>${title}</h3>

          <div class="ai-meta-grid">
            <div class="ai-meta-chip">
              <span>Brand</span>
              <strong>${brand}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>Variant</span>
              <strong>${variant}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>${retailerHeading}</span>
              <strong>${retailer}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>${priceStatusHeading}</span>
              <strong>${priceStatus}</strong>
            </div>
          </div>

          <div class="ai-metrics">
            <div class="ai-meter">
              <div class="ai-meter-row">
                <span>Requirement Match</span>
                <strong>${fitDisplay}</strong>
              </div>
              ${
                fitNumber != null
                  ? `
                    <div class="ai-meter-track">
                      <span class="ai-meter-fill" style="width:${fitNumber}%"></span>
                    </div>
                  `
                  : ""
              }
            </div>

            <div class="ai-meter">
              <div class="ai-meter-row">
                <span>Evidence Coverage</span>
                <strong>${evidenceDisplay}</strong>
              </div>
              ${
                evidenceNumber != null
                  ? `
                    <div class="ai-meter-track">
                      <span class="ai-meter-fill" style="width:${evidenceNumber}%"></span>
                    </div>
                  `
                  : ""
              }
            </div>
          </div>

          <p><strong>AI Confidence:</strong> ${confidence}</p>
          <p><strong>Price:</strong> ${price}</p>
          <p class="ai-last-checked"><strong>Last checked:</strong> ${lastChecked}</p>

          ${whyHTML}
          ${tradeoffsHTML}
          ${unknownsHTML}

          ${
            productLink !== "#"
              ? `
                <a
                  class="shop-button"
                  href="${productLink}"
                  target="_blank"
                  rel="nofollow sponsored noopener"
                  data-ai-retailer-click="1"
                  data-ai-rank="${escapeHTML(p.rank || "")}"
                  data-ai-product-id="${escapeHTML(
                    primaryOffer.product_id || p.product_id || ""
                  )}"
                  data-ai-retailer="${retailer}"
                >
                  ${offerCtaLabel}
                </a>
              `
              : `
                <p class="card-note">
                  Retailer link is currently unavailable.
                </p>
              `
          }
        </article>
      `;
    }).join("");

    card
      .querySelectorAll('a.shop-button[data-ai-retailer-click="1"]')
      .forEach(link => {
        link.addEventListener("click", () => {
          trackAnalyticsEvent("retailer_click", {
            search_term: analyticsQuery,
            product_id: link.dataset.aiProductId || "",
            retailer: link.dataset.aiRetailer || "",
            recommendation_rank: Number(link.dataset.aiRank || 0)
          });
        });
      });

  } catch (error) {
    console.error("Unable to load Shopping Brain response:", error);

    trackAnalyticsEvent("ai_search_error", {
      search_term: analyticsQuery,
      error_type: String(error && error.name || "Error").slice(0, 40)
    });

    card.innerHTML = `
      <h3>Recommendation temporarily unavailable</h3>
      <p>${escapeHTML(
        error.message || "Unable to reach Coupon World Shopping Intelligence."
      )}</p>
    `;
  }
}

loadShoppingRecommendation("");
