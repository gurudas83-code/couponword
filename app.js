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

  if (!cleanQuery) {
    card.innerHTML = `
      <h3>Ask Coupon World</h3>
      <p>Search for a product above to get personalized AI recommendations.</p>
    `;
    return;
  }

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

    if (recommendations.length === 0) {
      card.innerHTML = `
        <h3>No strong match found</h3>
        <p>Try changing the budget, RAM, storage, brand or other requirements.</p>
      `;
      return;
    }

    card.innerHTML = recommendations.map((p) => {
      const title = escapeHTML(p.title || "Recommended Product");
      const brand = escapeHTML(p.brand || "Not available");
      const fit =
        p.fit_percent != null ? escapeHTML(p.fit_percent) : "Not available";
      const confidence = escapeHTML(p.confidence || "unknown");

      const imageUrl = safeLink(p.image_url);

      const price =
        p.price != null
          ? `\u20B9${escapeHTML(p.price)}`
          : "Check latest price";

      const productLink = safeLink(
        p.market_source ||
        p.official_source ||
        p.link
      );

      const why = Array.isArray(p.why_it_fits)
        ? p.why_it_fits
        : [];

      const whyHTML = why.length
        ? `
          <ul class="ai-reasons">
            ${why.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
          </ul>
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

          <p><strong>Brand:</strong> ${brand}</p>
          <p><strong>Price:</strong> ${price}</p>
          <p><strong>Fit:</strong> ${fit}%</p>
          <p><strong>Confidence:</strong> ${confidence}</p>

          ${whyHTML}

          ${
            productLink !== "#"
              ? `
                <a
                  class="shop-button"
                  href="${productLink}"
                  target="_blank"
                  rel="nofollow sponsored noopener"
                >
                  Check Price \u2192
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

  } catch (error) {
    console.error("Unable to load Shopping Brain response:", error);

    card.innerHTML = `
      <h3>Recommendation temporarily unavailable</h3>
      <p>${escapeHTML(
        error.message || "Unable to reach Coupon World Shopping Intelligence."
      )}</p>
    `;
  }
}

loadShoppingRecommendation("");
