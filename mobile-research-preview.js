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
  var inventoryCards = [];
  var inventorySourceCounts = {};
  var verifiedRows = [];
  var CATALOGUE_INITIAL_LIMIT = 18;
  var TECHNICAL_FIELD_LABELS = {
    chipset: "Chipset",
    gpu: "GPU",
    display_type: "Display technology",
    display_inches: "Display size",
    display_resolution: "Display resolution",
    display_size_description: "Display size",
    display_resolution_description: "Display resolution",
    display_refresh_max_hz: "Refresh rate",
    display_refresh_description: "Refresh rate",
    display_type_description: "Display technology",
    rear_main_mp: "Main camera",
    rear_ultrawide_mp: "Ultrawide camera",
    rear_telephoto_mp: "Telephoto camera",
    front_mp: "Front camera",
    ois: "OIS",
    battery_mah_typical: "Battery capacity",
    wired_charging_max_w: "Wired charging",
    launch_android: "Launch Android",
    os_upgrade_generations: "OS updates",
    security_support_years: "Security updates",
    ip_rating: "IP rating",
    network_support: "5G/network support",
    rear_camera_system: "Rear camera system",
    front_camera_system: "Front camera system",
    battery_capacity_description: "Battery capacity",
    charging_description: "Charging support",
    battery_and_charging: "Battery and charging",
    operating_system: "Operating system",
    security_update_policy: "Security update policy",
    durability: "Durability"
  };

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

  function inventoryVariantStatus(row) {
    if (row && row.status) return String(row.status);
    if (row && String(row.manufacturer_spec_status || "").toUpperCase() === "VERIFIED") return "OFFICIAL_VERIFIED";
    return "RESEARCH_ONLY";
  }

  function inventoryRowsForCard(card) {
    var discovery = (card.discovery_record_keys || []).map(function (key) {
      return inventoryRows.find(function (row) { return row.record_key === key; });
    }).filter(Boolean);
    var frozen = (card.frozen_variant_ids || []).map(function (id) {
      return verifiedRows.find(function (row) { return row.canonical_product_id === id; });
    }).filter(Boolean);
    return discovery.concat(frozen);
  }

  function inventoryAllVariantRows() {
    return inventoryCards.reduce(function (all, card) { return all.concat(inventoryRowsForCard(card)); }, []);
  }

  function inventoryMatches(card) {
    var query = String(inventoryQuery && inventoryQuery.value || "").trim().toLowerCase();
    var brand = String(inventoryBrand && inventoryBrand.value || "");
    var ram = String(inventoryRam && inventoryRam.value || "");
    var storage = String(inventoryStorage && inventoryStorage.value || "");
    var status = String(inventoryStatus && inventoryStatus.value || "");
    var rows = inventoryRowsForCard(card);
    var haystack = (String(card.brand || "") + " " + String(card.model || "") + " " + rows.map(function (row) {
      return row.variant_text || ((row.ram_gb || "") + "GB " + (row.storage_gb || "") + "GB");
    }).join(" ")).toLowerCase();
    return (!query || haystack.indexOf(query) >= 0) &&
      (!brand || String(card.brand || "") === brand) &&
      (!ram || rows.some(function (row) { return String(row.ram_gb || "") === ram; })) &&
      (!storage || rows.some(function (row) { return String(row.storage_gb || "") === storage; })) &&
      (!status || rows.some(function (row) { return inventoryVariantStatus(row) === status; }));
  }

  function inventoryImage() {
    return '<div class="mobile-research-inventory-placeholder" role="img" aria-label="Product image not safely verified">Phone image unavailable</div>';
  }

  function renderInventoryCard(card) {
    var rows = inventoryRowsForCard(card);
    var discoveryRows = rows.filter(function (row) { return !row.canonical_product_id; });
    var frozenRows = rows.filter(function (row) { return !!row.canonical_product_id; });
    var statuses = Array.from(new Set(rows.map(inventoryVariantStatus)));
    var statusLabel = card.status || (statuses.length === 1 ? statuses[0] : "MIXED_EVIDENCE");
    var variantItems = rows.map(function (row) {
      var ram = row.ram_gb != null ? row.ram_gb + "GB RAM" : "RAM not specified";
      var storage = row.storage_gb != null ? row.storage_gb + "GB storage" : "storage not specified";
      if (row.canonical_product_id) return '<li><strong>Verified India variant</strong> · ' + escapeHtml(ram + " · " + storage) + ' · ' + escapeHtml(row.canonical_product_id) + '</li>';
      return '<li>Research variant · ' + escapeHtml(row.variant_text || (ram + " · " + storage)) + ' · ' + escapeHtml(inventoryVariantStatus(row)) + '</li>';
    }).join("");
    var fieldSet = {};
    discoveryRows.forEach(function (row) { (row.verified_fields || []).forEach(function (field) { fieldSet[String(field).replace(/_/g, " ")] = true; }); });
    var fields = Object.keys(fieldSet).join(", ") || "No exact fields verified in discovery record";
    var specSet = {};
    Object.keys(card.specifications || {}).forEach(function (key) {
      var item = card.specifications[key] || {};
      var label = String(item.label || key).replace(/_/g, " ");
      var value = specValue(key, item);
      if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
    });
    frozenRows.forEach(function (row) {
      Object.keys(row.specifications || {}).forEach(function (key) {
        var item = row.specifications[key] || {};
        var label = String(item.label || key).replace(/_/g, " ");
        var value = specValue(key, item);
        if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
      });
    });
    var frozenSpecs = Object.keys(specSet).slice(0, 8).map(function (entry) {
      var separator = entry.indexOf("|");
      return '<li><span>' + escapeHtml(entry.slice(0, separator)) + '</span><strong>' + escapeHtml(entry.slice(separator + 1)) + '</strong></li>';
    }).join("");
    var knownLabels = {};
    Object.keys(specSet).forEach(function (entry) {
      var separator = entry.indexOf("|");
      if (separator > 0) knownLabels[entry.slice(0, separator).toLowerCase()] = true;
    });
    var missingSpecs = [];
    (card.missing_specifications || []).forEach(function (key) {
      var label = TECHNICAL_FIELD_LABELS[key] || String(key).replace(/_/g, " ");
      if (!knownLabels[String(label).toLowerCase()] && missingSpecs.indexOf(label) < 0) missingSpecs.push(label);
    });
    var pending = missingSpecs.length ? '<p class="mobile-research-pending"><strong>Verification pending:</strong> ' + escapeHtml(missingSpecs.join(", ")) + '</p>' : '';
    var details = frozenSpecs ? '<p class="mobile-research-known"><strong>Source-backed specifications:</strong></p><ul class="mobile-research-model-specs">' + frozenSpecs + '</ul>' + pending : '<p>Source-backed technical specifications are not yet available for this model.</p>' + pending;
    var sourceUrls = [];
    discoveryRows.forEach(function (row) { (row.source_urls || []).forEach(function (url) { if (sourceUrls.indexOf(url) < 0) sourceUrls.push(url); }); });
    (card.source_urls || []).forEach(function (url) { if (sourceUrls.indexOf(url) < 0) sourceUrls.push(url); });
    frozenRows.forEach(function (row) { if (row.official_source && sourceUrls.indexOf(row.official_source) < 0) sourceUrls.push(row.official_source); });
    var sources = sourceUrls.slice(0, 3).map(function (url, index) { return link(url, index ? "Source" : "Official/source evidence"); }).join("");
    var counts = (discoveryRows.length ? discoveryRows.length + " research record" + (discoveryRows.length === 1 ? "" : "s") : "No discovery record") +
      (frozenRows.length ? " · " + frozenRows.length + " frozen exact variant" + (frozenRows.length === 1 ? "" : "s") : "");
    return '<article class="mobile-research-inventory-card mobile-research-model-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '">' +
      inventoryImage(card) +
      '<div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status inventory-status-' + escapeHtml(statusLabel.toLowerCase()) + '">' + escapeHtml(statusLabel) + '</span></div>' +
      '<h3>' + escapeHtml(card.brand + " " + card.model) + '</h3>' +
      '<p class="mobile-research-variant">' + escapeHtml(counts || "Model research reference") + '</p>' +
      '<ul class="mobile-research-variant-list">' + (variantItems || "<li>Variant details are not specified in the source universe.</li>") + '</ul>' +
      '<p class="mobile-research-inventory-fields"><strong>Verified fields:</strong> ' + escapeHtml(fields) + '</p>' +
      '<details class="mobile-research-model-details"><summary>View specifications / details</summary>' + details + '</details>' +
      '<p class="mobile-research-inventory-reason">Model card groups source-backed discovery records and frozen exact variants. It does not certify availability or purchase eligibility.</p>' +
      '<div class="mobile-research-sources">' + sources + '</div>' +
      '<p class="mobile-research-gate">Research only · no price · no stock · no purchase action</p>' +
      '</div></article>';
  }

  function renderInventory() {
    if (!inventoryGrid) return;
    var filtered = inventoryCards.filter(inventoryMatches);
    var matchingVariants = filtered.reduce(function (count, card) { return count + inventoryRowsForCard(card).length; }, 0);
    var isUnfiltered = !(inventoryQuery && inventoryQuery.value) && !(inventoryBrand && inventoryBrand.value) && !(inventoryRam && inventoryRam.value) && !(inventoryStorage && inventoryStorage.value) && !(inventoryStatus && inventoryStatus.value);
    if (inventoryCount) {
      inventoryCount.textContent = isUnfiltered && inventorySourceCounts.visible_model_cards ?
        inventorySourceCounts.visible_model_cards + " smartphone models · " + (inventorySourceCounts.deduplicated_discovery_records || inventoryRows.length) + " research records · " + (inventorySourceCounts.frozen_verified_variants || verifiedRows.length) + " frozen exact variants" :
        filtered.length + " smartphone models · " + matchingVariants + " matching research/frozen variants";
    }
    inventoryGrid.innerHTML = filtered.length ? filtered.map(renderInventoryCard).join("") : "<p>No smartphone models match these filters.</p>";
    if (inventoryMore) inventoryMore.hidden = true;
  }

  function refreshInventoryControls() {
    var rows = inventoryAllVariantRows();
    fillSelect(inventoryBrand, Array.from(new Set(inventoryCards.map(function (card) { return card.brand; }))).sort(), "All brands");
    fillSelect(inventoryRam, optionValues(rows, "ram_gb"), "All RAM");
    fillSelect(inventoryStorage, optionValues(rows, "storage_gb"), "All storage");
    fillSelect(inventoryStatus, ["OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"], "All evidence statuses");
    renderInventory();
  }

  function loadInventoryCatalogue() {
    if (!inventoryGrid) return;
    // Version the generated data URL so a reviewed catalogue refresh cannot
    // be hidden by a stale GitHub Pages/browser cache.
    fetch("/data/mobile_research_catalogue.json?v=20261101-1", { credentials: "omit" })
      .then(function (response) {
        if (!response.ok) throw new Error("research catalogue unavailable");
        return response.json();
      })
      .then(function (payload) {
        inventoryRows = Array.isArray(payload.records) ? payload.records : [];
        inventoryCards = Array.isArray(payload.model_cards) ? payload.model_cards : [];
        inventorySourceCounts = payload.source_counts || {};
        refreshInventoryControls();
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
      verifiedRows = products;
      grid.innerHTML = products.length ? products.map(renderProduct).join("") : "<p>Verified mobile research is currently unavailable.</p>";
      refreshInventoryControls();
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
  if (inventoryMore) inventoryMore.hidden = true;
  loadInventoryCatalogue();
}());
