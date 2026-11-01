(function () {
  "use strict";

  // This is a public, read-only research comparison. Live shopping remains on
  // the existing /api/recommend path and never consumes this dataset.
  var section = document.getElementById("mobileResearchPreview");
  var grid = document.getElementById("mobileResearchGrid");
  if (!section || !grid) return;

  var catalogueGrid = document.getElementById("catalogueDiscoveryGrid");
  var catalogueCount = document.getElementById("catalogueDiscoveryCount");
  var catalogueMore = document.getElementById("catalogueDiscoveryMore");
  var inventoryGrid = document.getElementById("mobileResearchCatalogueGrid");
  var inventoryCount = document.getElementById("mobileResearchCatalogueCount");
  var inventoryMore = document.getElementById("mobileResearchCatalogueMore");
  var inventoryQuery = document.getElementById("mobileResearchCatalogueQuery");
  var inventoryBrand = document.getElementById("mobileResearchCatalogueBrand");
  var inventoryRam = document.getElementById("mobileResearchCatalogueRam");
  var inventoryStorage = document.getElementById("mobileResearchCatalogueStorage");
  var inventoryStatus = document.getElementById("mobileResearchCatalogueStatus");
  var catalogueRows = [];
  var catalogueExpanded = false;
  var inventoryRows = [];
  var inventoryExpanded = false;
  var CATALOGUE_INITIAL_LIMIT = 18;
  var INVENTORY_INITIAL_LIMIT = 24;

  // The dataset has already passed the publish-safety checks. Keep the section
  // visible for normal visitors; commerce gates remain in the rendered cards.
  section.hidden = false;

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function link(url, label) {
    if (!/^https:\/\//i.test(String(url || ""))) return "";
    return '<a class="mobile-research-link" href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(label) + " ↗</a>";
  }

  function optionValues(rows, key) {
    var values = {};
    (rows || []).forEach(function (row) {
      if (row && row[key] != null && row[key] !== "") values[String(row[key])] = true;
    });
    return Object.keys(values).sort(function (a, b) { return Number(a) - Number(b) || a.localeCompare(b); });
  }

  function fillSelect(select, values, label) {
    if (!select) return;
    select.innerHTML = '<option value="">' + escapeHtml(label) + '</option>' + values.map(function (value) {
      return '<option value="' + escapeHtml(value) + '">' + escapeHtml(value) + '</option>';
    }).join("");
  }

  function inventoryMatches(row) {
    var query = String(inventoryQuery && inventoryQuery.value || "").trim().toLowerCase();
    var brand = String(inventoryBrand && inventoryBrand.value || "");
    var ram = String(inventoryRam && inventoryRam.value || "");
    var storage = String(inventoryStorage && inventoryStorage.value || "");
    var status = String(inventoryStatus && inventoryStatus.value || "");
    var haystack = (String(row.brand || "") + " " + String(row.model || "") + " " + String(row.variant_text || "")).toLowerCase();
    return (!query || haystack.indexOf(query) >= 0) &&
      (!brand || String(row.brand || "") === brand) &&
      (!ram || String(row.ram_gb || "") === ram) &&
      (!storage || String(row.storage_gb || "") === storage) &&
      (!status || String(row.status || "") === status);
  }

  function inventoryImage(row) {
    if (row.image_status === "VERIFIED_MATCH" && /^https:\/\//i.test(String(row.image_url || ""))) {
      return '<img class="mobile-research-inventory-image" src="' + escapeHtml(row.image_url) + '" alt="' + escapeHtml(row.brand + " " + row.model) + ' product image" loading="lazy">';
    }
    return '<div class="mobile-research-inventory-placeholder" role="img" aria-label="Product image not safely verified">Phone image unavailable</div>';
  }

  function renderInventoryRow(row) {
    var variant = row.variant_confidence === "official_exact" ?
      "India exact variant · " + (row.ram_gb || "") + "GB RAM · " + (row.storage_gb || "") + "GB storage" :
      "Research variant · " + escapeHtml(row.variant_text || "Variant not specified") + " (not verified)";
    var fields = (row.verified_fields || []).map(function (field) { return String(field).replace(/_/g, " "); }).join(", ") || "No verified fields";
    var sources = (row.source_urls || []).slice(0, 2).map(function (url, index) { return link(url, index ? "Discovery source" : "Source"); }).join("");
    return '<article class="mobile-research-inventory-card">' +
      inventoryImage(row) +
      '<div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status inventory-status-' + escapeHtml(String(row.status || "").toLowerCase()) + '">' + escapeHtml(row.status || "NEEDS_VERIFICATION") + '</span></div>' +
      '<h3>' + escapeHtml(row.brand + " " + row.model) + '</h3>' +
      '<p class="mobile-research-variant">' + variant + '</p>' +
      '<p class="mobile-research-inventory-fields"><strong>Verified fields:</strong> ' + escapeHtml(fields) + '</p>' +
      '<p class="mobile-research-inventory-reason">' + escapeHtml(row.status_reason || "Evidence status not stated") + '</p>' +
      '<div class="mobile-research-sources">' + sources + '</div>' +
      '<p class="mobile-research-gate">Research only · no price · no stock · no purchase action</p>' +
      '</div></article>';
  }

  function renderInventory() {
    if (!inventoryGrid) return;
    var filtered = inventoryRows.filter(inventoryMatches);
    var visible = inventoryExpanded ? filtered : filtered.slice(0, INVENTORY_INITIAL_LIMIT);
    inventoryGrid.innerHTML = visible.length ? visible.map(renderInventoryRow).join("") : "<p>No research records match these filters.</p>";
    if (inventoryCount) inventoryCount.textContent = filtered.length + " research records";
    if (inventoryMore) {
      inventoryMore.hidden = filtered.length <= INVENTORY_INITIAL_LIMIT;
      inventoryMore.textContent = inventoryExpanded ? "Show fewer research records" : "Show all research records";
    }
  }

  function loadInventoryCatalogue() {
    if (!inventoryGrid) return;
    fetch("/data/mobile_research_catalogue.json", { credentials: "omit" })
      .then(function (response) {
        if (!response.ok) throw new Error("research catalogue unavailable");
        return response.json();
      })
      .then(function (payload) {
        inventoryRows = Array.isArray(payload.records) ? payload.records : [];
        fillSelect(inventoryBrand, Array.from(new Set(inventoryRows.map(function (row) { return row.brand; }))).sort(), "All brands");
        fillSelect(inventoryRam, optionValues(inventoryRows, "ram_gb"), "All RAM");
        fillSelect(inventoryStorage, optionValues(inventoryRows, "storage_gb"), "All storage");
        fillSelect(inventoryStatus, ["OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"], "All evidence statuses");
        renderInventory();
      })
      .catch(function () {
        if (inventoryCount) inventoryCount.textContent = "Research catalogue unavailable";
        inventoryGrid.innerHTML = "<p>Existing research records are currently unavailable.</p>";
      });
  }

  function specValue(key, item) {
    var value = item && item.value;
    if (key === "display_inches") return value + " in";
    if (key === "display_refresh_max_hz") return value + " Hz";
    if (["rear_main_mp", "rear_ultrawide_mp", "front_mp"].indexOf(key) >= 0) return value + " MP";
    if (key === "battery_mah_typical") return value + " mAh";
    if (key === "wired_charging_max_w") return value + " W";
    if (key === "os_upgrade_generations") return value + " Android generations";
    if (key === "security_support_years") return value + " years";
    return value;
  }

  function metricNames(metrics) {
    return (metrics || []).map(function (metric) {
      return String(metric).replace(/_/g, " ");
    }).join(", ") || "No accepted measurement";
  }

  function catalogueStatus(row) {
    var identityVerified = row && (row.identity_verified === true || String(row.catalog_status || "").toLowerCase() === "verified");
    return identityVerified ? "Identity verified · no current offer" : "Historical / unverified reference";
  }

  function safeCatalogueRows(rows) {
    return (Array.isArray(rows) ? rows : []).filter(function (row) {
      var keys = Object.keys(row || {});
      return row && typeof row === "object" && row.id != null && String(row.title || "").trim() &&
        !keys.some(function (key) { return /private|secret|credential|output|report/i.test(String(key)); });
    }).map(function (row) {
      return {
        id: String(row.id),
        title: String(row.title || "").trim().slice(0, 180),
        brand: String(row.brand || "").trim().slice(0, 80),
        category: String(row.category || "Catalogue").trim().slice(0, 80),
        status: catalogueStatus(row)
      };
    });
  }

  function renderCatalogueRow(row) {
    return '<article class="catalogue-reference-card">' +
      '<div class="catalogue-reference-top"><span class="research-id">Catalogue #' + escapeHtml(row.id) + '</span><span class="catalogue-status">' + escapeHtml(row.status) + '</span></div>' +
      '<h3>' + escapeHtml(row.title) + '</h3>' +
      '<p><strong>' + escapeHtml(row.brand || "Brand not stated") + '</strong> · ' + escapeHtml(row.category) + '</p>' +
      '<p class="catalogue-reference-note">Reference listing only. Exact identity, price, stock and purchase eligibility are not asserted.</p>' +
      '</article>';
  }

  function renderCatalogueRows() {
    if (!catalogueGrid) return;
    var visible = catalogueExpanded ? catalogueRows : catalogueRows.slice(0, CATALOGUE_INITIAL_LIMIT);
    catalogueGrid.innerHTML = visible.length ? visible.map(renderCatalogueRow).join("") : "<p>Catalogue references are currently unavailable.</p>";
    if (catalogueMore) {
      catalogueMore.hidden = catalogueRows.length <= CATALOGUE_INITIAL_LIMIT;
      catalogueMore.textContent = catalogueExpanded ? "Show fewer catalogue references" : "Show all catalogue references";
    }
  }

  function renderProduct(product) {
    var specs = product.specifications || {};
    var specHtml = Object.keys(specs).map(function (key) {
      var item = specs[key] || {};
      return '<li><span>' + escapeHtml(item.label || key) + '</span><strong>' + escapeHtml(specValue(key, item)) + '</strong></li>';
    }).join("");
    var battery = product.battery_evidence || {};
    var camera = product.camera_evidence || {};
    var cameraScope = (camera.scope || []).join(", ").replace(/_/g, " ");
    return '<article class="mobile-research-card">' +
      '<div class="mobile-research-card-top"><span class="research-id">' + escapeHtml(product.canonical_product_id) + '</span><span class="research-status">' + escapeHtml(product.manufacturer_spec_status || "UNAVAILABLE") + '</span></div>' +
      '<h3>' + escapeHtml(product.brand + " " + product.model) + '</h3>' +
      '<p class="mobile-research-variant">India · ' + escapeHtml(product.ram_gb) + 'GB RAM · ' + escapeHtml(product.storage_gb) + 'GB storage</p>' +
      '<ul class="mobile-research-specs">' + specHtml + '</ul>' +
      '<p class="mobile-research-lane"><strong>Technical lane:</strong> ' + escapeHtml(product.technical_lane) + '</p>' +
      '<div class="mobile-research-evidence"><p><strong>Battery:</strong> ' + escapeHtml(battery.status || "Unavailable") + ' · ' + escapeHtml(metricNames(battery.metrics)) + ' <span class="research-scope">(' + escapeHtml(battery.applicability || "scope not stated") + ')</span></p>' +
      '<p><strong>Camera:</strong> ' + escapeHtml(camera.status || "Unavailable") + ' · ' + escapeHtml((camera.observation_types || []).join(", ").replace(/_/g, " ") || "No accepted observation") + ' <span class="research-scope">(' + escapeHtml(cameraScope || "scope not stated") + ')</span></p></div>' +
      '<div class="mobile-research-sources">' + link(product.official_source, "Official source") + (battery.source_urls && battery.source_urls[0] ? link(battery.source_urls[0], "Battery source") : "") + (camera.source_urls && camera.source_urls[0] ? link(camera.source_urls[0], "Camera source") : "") + '</div>' +
      '<p class="mobile-research-gate">No live offer · no price · no purchase action</p>' +
      '</article>';
  }

  fetch("/data/mobile_research_preview.json", { credentials: "omit" })
    .then(function (response) {
      if (!response.ok) throw new Error("research preview unavailable");
      return response.json();
    })
    .then(function (payload) {
      var products = Array.isArray(payload.products) ? payload.products : [];
      grid.innerHTML = products.length ? products.map(renderProduct).join("") : "<p>Verified mobile research is currently unavailable.</p>";
    })
    .catch(function () {
      grid.innerHTML = "<p>Verified mobile research is currently unavailable.</p>";
    });

  if (catalogueGrid) {
    fetch("/coupons.json", { credentials: "omit" })
      .then(function (response) {
        if (!response.ok) throw new Error("catalogue unavailable");
        return response.json();
      })
      .then(function (rows) {
        catalogueRows = safeCatalogueRows(rows);
        if (catalogueCount) catalogueCount.textContent = catalogueRows.length + " catalogue references";
        renderCatalogueRows();
      })
      .catch(function () {
        if (catalogueCount) catalogueCount.textContent = "No catalogue references available";
        catalogueGrid.innerHTML = "<p>Catalogue references are currently unavailable.</p>";
      });
    if (catalogueMore) {
      catalogueMore.addEventListener("click", function () {
        catalogueExpanded = !catalogueExpanded;
        renderCatalogueRows();
      });
    }
  }

  [inventoryQuery, inventoryBrand, inventoryRam, inventoryStorage, inventoryStatus].forEach(function (control) {
    if (control) control.addEventListener("input", renderInventory);
    if (control && control.tagName === "SELECT") control.addEventListener("change", renderInventory);
  });
  if (inventoryMore) {
    inventoryMore.addEventListener("click", function () {
      inventoryExpanded = !inventoryExpanded;
      renderInventory();
    });
  }
  loadInventoryCatalogue();
}());
