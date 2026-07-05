// Coupon World v4.0 — Deal discovery app
const DATA_URL = "coupons.json";

let allDeals = [];
let categories = ["All"];
let activeCategory = "All";
let searchTerm = "";
let sortMode = "latest";
let viewMode = "grid";

const els = {
  heroSearch: document.getElementById("heroSearch"),
  heroSearchButton: document.getElementById("heroSearchButton"),
  searchInput: document.getElementById("searchInput"),
  sortSelect: document.getElementById("sortSelect"),
  categoryChips: document.getElementById("categoryChips"),
  dealsGrid: document.getElementById("dealsGrid"),
  resultsCount: document.getElementById("resultsCount"),
  featuredDeal: document.getElementById("featuredDeal"),
  statDeals: document.getElementById("statDeals"),
  statCategories: document.getElementById("statCategories")
};

const clean = (value, fallback = "") => {
  if (value === null || value === undefined || String(value).trim() === "") return fallback;
  return String(value).trim();
};

const escapeHtml = (str) => String(str ?? "").replace(/[&<>"']/g, (m) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "\"": "&quot;",
  "'": "&#039;"
}[m]));

const toNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const n = parseFloat(String(value).replace(/[^\d.]/g, ""));
  return Number.isFinite(n) ? n : null;
};

const rupees = (num) => "₹" + Number(num).toLocaleString("en-IN", { maximumFractionDigits: 0 });

const discountNumber = (text) => {
  const match = String(text || "").match(/(\d+(\.\d+)?)/);
  return match ? parseFloat(match[1]) : -1;
};

async function loadDeals() {
  try {
    const response = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    if (!Array.isArray(data)) throw new Error("coupons.json must be a JSON array.");

    allDeals = data
      .filter((deal) => deal && deal.title && deal.link)
      .map(normalizeDeal);

    categories = ["All", ...new Set(allDeals.map((d) => d.category || "Deals"))].slice(0, 30);

    els.statDeals.textContent = allDeals.length;
    els.statCategories.textContent = Math.max(categories.length - 1, 0);

    buildCategoryChips();
    renderFeaturedDeal();
    renderDeals();
  } catch (error) {
    els.resultsCount.textContent = "No deals loaded";
    els.dealsGrid.innerHTML = `
      <div class="state-card">
        <strong>Could not load deals</strong>
        <span>${escapeHtml(error.message)}. Check coupons.json.</span>
      </div>
    `;
  }
}

function normalizeDeal(deal) {
  return {
    id: deal.id ?? "",
    store: clean(deal.store, "Amazon IN"),
    category: clean(deal.category, "Deals"),
    title: clean(deal.title, "Untitled deal"),
    discount: clean(deal.discount, "Check Deal"),
    code: clean(deal.code, "NO CODE NEEDED"),
    link: clean(deal.link, "#"),
    expiry: clean(deal.expiry, "Limited Time"),
    image: clean(deal.image, ""),
    description: clean(deal.description, "Click to check the latest price and availability on Amazon."),
    price: deal.price,
    mrp: deal.mrp,
    save: deal.save
  };
}

function buildCategoryChips() {
  els.categoryChips.innerHTML = categories.map((category) => `
    <button class="chip ${category === activeCategory ? "active" : ""}" type="button" data-category="${escapeHtml(category)}">
      ${escapeHtml(category)}
    </button>
  `).join("");

  els.categoryChips.querySelectorAll(".chip").forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.category;
      buildCategoryChips();
      renderDeals();
      document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
    });
  });
}

function getFilteredDeals() {
  const term = searchTerm.trim().toLowerCase();

  let list = allDeals.filter((deal) => {
    if (activeCategory !== "All" && deal.category !== activeCategory) return false;

    if (!term) return true;

    return [
      deal.title,
      deal.store,
      deal.category,
      deal.discount,
      deal.code,
      deal.description
    ].join(" ").toLowerCase().includes(term);
  });

  if (sortMode === "az") {
    list.sort((a, b) => a.title.localeCompare(b.title));
  }

  if (sortMode === "discount") {
    list.sort((a, b) => discountNumber(b.discount) - discountNumber(a.discount));
  }

  return list;
}

function renderFeaturedDeal() {
  const deal =
    allDeals.find((d) => toNumber(d.price) !== null && d.image) ||
    allDeals.find((d) => d.image) ||
    allDeals[0];

  if (!deal) return;

  const price = toNumber(deal.price);
  const mrp = toNumber(deal.mrp);

  els.featuredDeal.innerHTML = `
    ${imageBlock(deal, "spotlight-image")}
    <h2>${escapeHtml(deal.title)}</h2>
    <p>${price !== null ? rupees(price) : escapeHtml(deal.discount)} ${mrp ? `<span class="inline-mrp">${rupees(mrp)}</span>` : ""}</p>
    <a href="${escapeHtml(deal.link)}" target="_blank" rel="nofollow sponsored noopener">Shop Now →</a>
  `;
}

function renderDeals() {
  const list = getFilteredDeals();

  els.resultsCount.textContent = `${list.length} deal${list.length === 1 ? "" : "s"} found`;
  els.dealsGrid.classList.toggle("compact", viewMode === "compact");

  if (list.length === 0) {
    els.dealsGrid.innerHTML = `
      <div class="state-card">
        <strong>No deals found</strong>
        <span>Try another search term or select All categories.</span>
      </div>
    `;
    return;
  }

  els.dealsGrid.innerHTML = list.map(dealCard).join("");
}

function imageBlock(deal, className = "deal-image") {
  if (deal.image) {
    return `
      <div class="${className}">
        <img src="${escapeHtml(deal.image)}" alt="${escapeHtml(deal.title)}" loading="lazy"
          onerror="this.parentElement.innerHTML='<div class=&quot;placeholder&quot;>🛍️<small>Coupon World</small></div>'">
      </div>
    `;
  }

  return `<div class="${className}"><div class="placeholder">🛍️<small>Coupon World</small></div></div>`;
}

function priceRow(deal) {
  const price = toNumber(deal.price);
  const mrp = toNumber(deal.mrp);
  const save = toNumber(deal.save);

  if (price === null && mrp === null && save === null) return "";

  return `
    <div class="price-row">
      ${price !== null ? `<span class="price">${rupees(price)}</span>` : ""}
      ${mrp !== null && mrp > 0 ? `<span class="mrp">${rupees(mrp)}</span>` : ""}
      ${save !== null && save > 0 ? `<span class="save">Save ${rupees(save)}</span>` : ""}
    </div>
  `;
}

function dealCard(deal) {
  return `
    <article class="deal-card">
      ${imageBlock(deal)}

      <div class="deal-meta">
        <span class="store">${escapeHtml(deal.store)}</span>
        <span class="category-pill">${escapeHtml(deal.category)}</span>
      </div>

      <h3 class="deal-title">${escapeHtml(deal.title)}</h3>
      <div class="discount">${escapeHtml(deal.discount)}</div>

      ${priceRow(deal)}

      <p class="description">${escapeHtml(deal.description)}</p>

      <div class="code-row">
        <span>${escapeHtml(deal.code)}</span>
        <span>${escapeHtml(deal.expiry)}</span>
      </div>

      <a class="shop-button" href="${escapeHtml(deal.link)}" target="_blank" rel="nofollow sponsored noopener">
        Shop Now →
      </a>

      <div class="card-note">Final price may change on Amazon.</div>
    </article>
  `;
}

function applySearch(term) {
  searchTerm = term;
  els.searchInput.value = term;
  els.heroSearch.value = term;
  renderDeals();
  document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
}

function applyCategory(category) {
  activeCategory = category;
  if (!categories.includes(category)) activeCategory = "All";
  buildCategoryChips();
  renderDeals();
  document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
}

els.searchInput.addEventListener("input", (event) => {
  searchTerm = event.target.value;
  els.heroSearch.value = searchTerm;
  renderDeals();
});

els.heroSearch.addEventListener("input", (event) => {
  searchTerm = event.target.value;
  els.searchInput.value = searchTerm;
  renderDeals();
});

els.heroSearchButton.addEventListener("click", () => applySearch(els.heroSearch.value));

els.heroSearch.addEventListener("keydown", (event) => {
  if (event.key === "Enter") applySearch(els.heroSearch.value);
});

els.sortSelect.addEventListener("change", (event) => {
  sortMode = event.target.value;
  renderDeals();
});

document.querySelectorAll("[data-search]").forEach((el) => {
  el.addEventListener("click", () => {
    const term = el.dataset.search;
    if (term === "discount") {
      sortMode = "discount";
      els.sortSelect.value = "discount";
      applySearch("");
    } else {
      applySearch(term);
    }
  });
});

document.querySelectorAll("[data-quick]").forEach((el) => {
  el.addEventListener("click", () => applyCategory(el.dataset.quick));
});

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    viewMode = button.dataset.view;
    document.querySelectorAll("[data-view]").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    renderDeals();
  });
});

loadDeals();
