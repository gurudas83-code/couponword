(function () {
  "use strict";

  // This is a public, read-only research comparison. Live shopping remains on
  // the existing /api/recommend path and never consumes this dataset.
  var section = document.getElementById("mobileResearchPreview");
  var grid = document.getElementById("mobileResearchGrid");
  if (!section || !grid) return;

  var searchSection = document.getElementById("mobileResearchSearch");
  var researchQuery = document.getElementById("mobileResearchQuery");
  var researchSearchButton = document.getElementById("mobileResearchSearchButton");
  var researchResults = document.getElementById("mobileResearchResults");
  var researchResultsMore = document.getElementById("mobileResearchResultsMore");
  var researchSearchStatus = document.getElementById("mobileResearchSearchStatus");
  var researchNewSection = document.getElementById("mobileResearchNew");
  var researchNewGrid = document.getElementById("mobileResearchNewGrid");
  var detailSection = document.getElementById("mobileResearchDetail");
  var detailContent = document.getElementById("mobileResearchDetailContent");
  var detailTitle = document.getElementById("mobileResearchDetailTitle");

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
  var INVENTORY_PAGE_SIZE = 18;
  var MAX_SEARCH_RESULTS = 6;
  var inventoryExpanded = false;
  var searchExpanded = false;
  var lastSearchQuery = "";
  var lastSearchMatches = [];
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

  // Keep the research catalogue out of the idle homepage. It is revealed by an
  // explicit search, comparison link, or Browse All action.
  section.hidden = true;
  var catalogueSection = document.getElementById("mobileResearchCatalogue");
  if (catalogueSection) catalogueSection.hidden = true;

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
    var launch = card.india_launch_date ? '<p class="mobile-research-launch"><strong>Verified India launch:</strong> ' + escapeHtml(card.india_launch_date) + '</p>' : '';
    return '<article class="mobile-research-inventory-card mobile-research-model-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '">' +
      inventoryImage(card) +
      '<div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status inventory-status-' + escapeHtml(statusLabel.toLowerCase()) + '">' + escapeHtml(statusLabel) + '</span></div>' +
      '<h3>' + escapeHtml(card.brand + " " + card.model) + '</h3>' + launch +
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
    var visible = inventoryExpanded ? filtered : filtered.slice(0, INVENTORY_PAGE_SIZE);
    inventoryGrid.innerHTML = visible.length ? visible.map(renderInventoryCard).join("") : "<p>No smartphone models match these filters.</p>";
    if (inventoryMore) {
      inventoryMore.hidden = filtered.length <= INVENTORY_PAGE_SIZE;
      inventoryMore.textContent = inventoryExpanded ? "Show fewer research models" : "Load more research models";
    }
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
        renderNewNoteworthy();
        handleResearchHash();
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

  function normalizeResearch(value) {
    return String(value == null ? "" : value).toLowerCase()
      .replace(/[’']/g, "")
      .replace(/[^a-z0-9\u0900-\u097f]+/g, " ")
      .replace(/\s+/g, " ").trim();
  }

  function researchRowsFor(card, query) {
    var rows = inventoryRowsForCard(card);
    var numbers = [];
    var match;
    var numberPattern = /\b(\d{1,2}|\d{3,4})\s*gb\b/gi;
    while ((match = numberPattern.exec(String(query || "")))) numbers.push(Number(match[1]));
    var ramMatch = String(query || "").match(/(\d{1,2})\s*gb\s*ram/i);
    var storageMatch = String(query || "").match(/(\d{2,4})\s*gb\s*(?:storage|rom)/i);
    var ram = ramMatch ? Number(ramMatch[1]) : (numbers.length > 1 ? numbers[0] : null);
    var storage = storageMatch ? Number(storageMatch[1]) : (numbers.length > 1 ? numbers[1] : null);
    if (ram == null && storage == null) return rows;
    return rows.filter(function (row) {
      var ramOK = ram == null || Number(row.ram_gb) === ram;
      var storageOK = storage == null || Number(row.storage_gb) === storage;
      return ramOK && storageOK;
    });
  }

  function excludedBrand(query) {
    var beforeMarker = String(query || "").match(/\b([a-z][a-z0-9/&-]*)\s+(?:ko\s+)?(?:chhodkar|chhod|छोड़कर|छोड़|हटाकर|के\s+बिना|बिना)\b/i);
    if (beforeMarker) return normalizeResearch(beforeMarker[1]);
    var match = String(query || "").match(/(?:exclude|excluding|without|except|no|chhodkar|chhod|छोड़कर|छोड़|हटाकर|के बिना)\s+([a-z][a-z0-9/& -]{1,30})/i);
    if (!match) return "";
    return normalizeResearch(match[1]).split(" ")[0];
  }

  function researchFeatureKeys(query) {
    var text = normalizeResearch(query);
    var keys = [];
    var groups = [
      [/camera|कैमरा/, ["rear_main_mp", "rear_camera_system", "front_camera_system", "ois"]],
      [/battery|बैटरी/, ["battery_mah_typical", "battery_capacity_description", "battery_and_charging", "wired_charging_max_w"]],
      [/gaming|game|गेमिंग/, ["gpu", "chipset"]],
      [/software|android|update|support|सॉफ्टवेयर/, ["operating_system", "launch_android", "os_upgrade_generations", "security_update_policy", "security_support_years"]],
      [/display|screen|डिस्प्ले/, ["display_type", "display_inches", "display_resolution", "display_refresh_max_hz"]]
    ];
    groups.forEach(function (group) { if (group[0].test(text)) keys = keys.concat(group[1]); });
    return Array.from(new Set(keys));
  }

  function researchSpecKeys(card, rows) {
    var keys = Object.keys(card.specifications || {});
    (rows || []).forEach(function (row) { keys = keys.concat(Object.keys(row.specifications || {})); });
    return keys;
  }

  function researchMatches(card, query) {
    var text = normalizeResearch(query);
    var excluded = excludedBrand(text);
    var brand = normalizeResearch(card.brand);
    if (excluded && brand.indexOf(excluded) >= 0) return [];
    var rows = researchRowsFor(card, query);
    if (!rows.length) return [];
    var haystack = normalizeResearch(card.brand + " " + card.model + " " + rows.map(function (row) {
      return row.variant_text || ((row.ram_gb || "") + "gb " + (row.storage_gb || "") + "gb");
    }).join(" "));
    var featureKeys = researchFeatureKeys(text);
    var stop = /^(best|good|phone|mobile|smartphone|under|below|within|price|in|the|and|with|ram|storage|camera|battery|gaming|game|software|support|display|screen|ko|ke|bina|chhodkar|chhod|का|के|में|अच्छा|फोन|मोबाइल)$/;
    var modelTokens = text.split(" ").filter(function (token) { return token && !stop.test(token) && !/^\d+$/.test(token) && token !== "gb" && token !== "exclude" && token !== "excluding" && token !== "without" && token !== "except" && token !== "no"; });
    var identityTokens = modelTokens.filter(function (token) { return !/^(chhodkar|chhod|छोड़कर|छोड़|हटाकर|के|बिना)$/.test(token) && token !== excluded && !/^\d+gb$/.test(token); });
    var identityMatch = identityTokens.length > 0 && identityTokens.every(function (token) { return haystack.indexOf(token) >= 0; });
    var broadMatch = featureKeys.length > 0 && featureKeys.some(function (key) { return researchSpecKeys(card, rows).indexOf(key) >= 0; });
    var brandOnly = identityTokens.length === 1 && (brand.indexOf(identityTokens[0]) >= 0 || haystack.indexOf(identityTokens[0]) >= 0);
    var hardVariantOnly = /\b\d{1,2}\s*gb(?:\s*ram)?\b/i.test(String(query || "")) || /\b\d{2,4}\s*gb\s*(?:storage|rom)?\b/i.test(String(query || ""));
    var exclusionOnly = Boolean(excluded) && identityTokens.length === 0 && featureKeys.length === 0;
    if (!identityMatch && !broadMatch && !brandOnly && !(hardVariantOnly && identityTokens.length === 0) && !exclusionOnly) return [];
    if (featureKeys.length && !broadMatch && !identityMatch) return [];
    return rows;
  }

  function renderResearchResultCard(card, rows) {
    var status = card.status || "RESEARCH_ONLY";
    var variants = rows.map(function (row) {
      return (row.ram_gb != null ? row.ram_gb + "GB RAM" : "RAM not specified") + " · " + (row.storage_gb != null ? row.storage_gb + "GB storage" : "storage not specified");
    });
    var specs = Object.keys(card.specifications || {}).slice(0, 4).map(function (key) {
      var item = card.specifications[key] || {};
      return '<li><span>' + escapeHtml(item.label || key.replace(/_/g, " ")) + '</span><strong>' + escapeHtml(specValue(key, item)) + '</strong></li>';
    }).join("");
    var launch = card.india_launch_date ? '<p class="mobile-research-launch"><strong>Verified India launch:</strong> ' + escapeHtml(card.india_launch_date) + '</p>' : '';
    var launchSource = card.india_launch_source ? link(card.india_launch_source, "India launch source") : "";
    return '<article class="mobile-research-inventory-card mobile-research-result-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '">' +
      inventoryImage(card) + '<div class="mobile-research-inventory-body"><div class="mobile-research-card-top"><span class="research-status">' + escapeHtml(status) + '</span><span class="research-status">Research only</span></div>' +
      '<h3>' + escapeHtml(card.brand + " " + card.model) + '</h3>' + launch + '<p class="mobile-research-variant">Matching documented variant' + (variants.length > 1 ? "s" : "") + ': ' + escapeHtml(variants.join(" · ")) + '</p>' +
      (specs ? '<ul class="mobile-research-model-specs">' + specs + '</ul>' : '<p>Technical specifications are pending verification.</p>') +
      '<div class="mobile-research-sources">' + launchSource + '</div>' +
      '<button type="button" class="btn btn-ghost mobile-research-detail-button" data-research-detail="' + escapeHtml(card.model_key) + '">View details</button>' +
      '<p class="mobile-research-gate">No price · no stock · no purchase action</p></div></article>';
  }

  function sortResearchMatches(matches, query) {
    var text = normalizeResearch(query);
    return matches.slice().sort(function (a, b) {
      var aExact = normalizeResearch(a.card.brand + " " + a.card.model) === text ? 1 : 0;
      var bExact = normalizeResearch(b.card.brand + " " + b.card.model) === text ? 1 : 0;
      if (aExact !== bExact) return bExact - aExact;
      var aEvidence = Object.keys(a.card.specifications || {}).length;
      var bEvidence = Object.keys(b.card.specifications || {}).length;
      return bEvidence - aEvidence || String(a.card.model).localeCompare(String(b.card.model));
    });
  }

  function searchResearch(query) {
    lastSearchQuery = String(query || "").trim();
    searchExpanded = false;
    if (!lastSearchQuery) {
      if (researchResults) { researchResults.hidden = true; researchResults.innerHTML = ""; }
      if (researchResultsMore) researchResultsMore.hidden = true;
      if (researchSearchStatus) researchSearchStatus.textContent = "";
      return [];
    }
    revealSearch();
    if (/\b(?:compare|vs|versus)\b/i.test(lastSearchQuery)) {
      if (researchResults) {
        researchResults.hidden = false;
        researchResults.innerHTML = '<p class="mobile-research-empty">Comparison queries use the existing evidence-backed comparison route below. No shopping ranking or price claim is added.</p>';
      }
      if (researchSearchStatus) researchSearchStatus.textContent = "Comparison request routed to evidence-backed research";
      if (researchResultsMore) researchResultsMore.hidden = true;
      return [];
    }
    var matches = sortResearchMatches(inventoryCards.map(function (card) {
      var rows = researchMatches(card, lastSearchQuery);
      return rows.length ? { card: card, rows: rows } : null;
    }).filter(Boolean), lastSearchQuery);
    lastSearchMatches = matches;
    var visible = searchExpanded ? matches : matches.slice(0, MAX_SEARCH_RESULTS);
    if (researchResults) {
      researchResults.hidden = false;
      researchResults.innerHTML = visible.length ? visible.map(function (item) { return renderResearchResultCard(item.card, item.rows); }).join("") : '<p class="mobile-research-empty">No matching research model was found. Try a model name, feature or Browse All Research.</p>';
    }
    if (researchSearchStatus) {
      var budget = /(?:under|below|within|ke|andar)\s*₹?\s*[0-9]/i.test(lastSearchQuery);
      researchSearchStatus.textContent = matches.length + " matching research model" + (matches.length === 1 ? "" : "s") + " · showing " + visible.length + (budget ? " · prices/offers are unavailable, so this is unpriced research only" : "");
    }
    if (researchResultsMore) { researchResultsMore.hidden = matches.length <= MAX_SEARCH_RESULTS; researchResultsMore.textContent = searchExpanded ? "Show fewer results" : "Load more research results"; }
    return matches;
  }

  function revealSearch() {
    if (searchSection) searchSection.hidden = false;
  }

  function revealPreview() {
    section.hidden = false;
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function revealCatalogue() {
    if (catalogueSection) catalogueSection.hidden = false;
    if (catalogueSection) catalogueSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showDetail(modelKey) {
    var card = inventoryCards.find(function (item) { return item.model_key === modelKey; });
    if (!card || !detailSection || !detailContent) return;
    detailSection.hidden = false;
    if (detailTitle) detailTitle.textContent = card.brand + " " + card.model;
    detailContent.innerHTML = renderInventoryCard(card) + '<p class="mobile-research-gate">Research detail only · no current offer, price or purchase action.</p>';
    detailSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function handleResearchHash() {
    var hash = String(window.location.hash || "");
    if (hash === "#mobileResearchPreview") revealPreview();
    if (hash === "#mobileResearchCatalogue") revealCatalogue();
    if (hash.indexOf("#mobileResearchDetail/") === 0) showDetail(decodeURIComponent(hash.slice("#mobileResearchDetail/".length)));
  }

  function renderNewNoteworthy() {
    if (!researchNewSection || !researchNewGrid) return;
    var now = Date.now();
    var recent = inventoryCards.filter(function (card) {
      var date = card.india_launch_date || card.launch_date_india || card.launch_date;
      var time = Date.parse(String(date || ""));
      return card.status === "OFFICIAL_VERIFIED" && Number.isFinite(time) && now - time >= 0 && now - time <= 365 * 24 * 60 * 60 * 1000 && (card.source_urls || []).length;
    }).sort(function (a, b) { return Date.parse(b.india_launch_date || b.launch_date_india || b.launch_date) - Date.parse(a.india_launch_date || a.launch_date_india || a.launch_date); }).slice(0, 6);
    researchNewSection.hidden = recent.length === 0;
    researchNewGrid.innerHTML = recent.map(function (card) { return renderResearchResultCard(card, inventoryRowsForCard(card)); }).join("");
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
      renderNewNoteworthy();
      handleResearchHash();
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
    if (control) control.addEventListener("input", function () { inventoryExpanded = false; renderInventory(); });
    if (control && control.tagName === "SELECT") control.addEventListener("change", function () { inventoryExpanded = false; renderInventory(); });
  });
  if (inventoryMore) inventoryMore.addEventListener("click", function () { inventoryExpanded = !inventoryExpanded; renderInventory(); });
  if (researchSearchButton) researchSearchButton.addEventListener("click", function () { searchResearch(researchQuery && researchQuery.value); });
  if (researchQuery) researchQuery.addEventListener("keydown", function (event) { if (event.key === "Enter") searchResearch(researchQuery.value); });
  document.querySelectorAll("[data-mobile-research-query]").forEach(function (button) {
    button.addEventListener("click", function () { if (researchQuery) researchQuery.value = button.getAttribute("data-mobile-research-query") || ""; searchResearch(researchQuery && researchQuery.value); });
  });
  if (researchResultsMore) researchResultsMore.addEventListener("click", function () { searchExpanded = !searchExpanded; searchResearch(lastSearchQuery); });
  document.addEventListener("click", function (event) {
    var detail = event.target.closest("[data-research-detail]");
    if (detail) {
      event.preventDefault();
      window.location.hash = "mobileResearchDetail/" + encodeURIComponent(detail.getAttribute("data-research-detail"));
      showDetail(detail.getAttribute("data-research-detail"));
    }
    var linkTarget = event.target.closest('a[href="#mobileResearchPreview"], a[href="#mobileResearchCatalogue"]');
    if (linkTarget) {
      if (linkTarget.getAttribute("href") === "#mobileResearchPreview") revealPreview();
      if (linkTarget.getAttribute("href") === "#mobileResearchCatalogue") revealCatalogue();
    }
  });
  window.addEventListener("hashchange", handleResearchHash);
  window.CouponWorldMobileResearch = {
    isResearchQuery: function (value) {
      return /(?:phone|mobile|smartphone|galaxy|samsung|iphone|pixel|redmi|oneplus|nothing|realme|vivo|oppo|xiaomi|motorola|poco|iqoo|lava|tecno|infinix|camera|battery|gaming|display|software|android|ram|storage|फोन|मोबाइल|कैमरा|बैटरी|गेमिंग|सैमसंग|अच्छा)/i.test(String(value || ""));
    },
    search: searchResearch,
    clear: function () { if (researchQuery) researchQuery.value = ""; searchResearch(""); },
    revealPreview: revealPreview,
    revealCatalogue: revealCatalogue
  };
  loadInventoryCatalogue();
}());
