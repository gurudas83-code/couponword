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
  var inventoryByKey = new Map();
  var verifiedById = new Map();
  var inventoryCards = [];
  var marketIntakeCount = 0;
  var inventoryLoadFailed = false;
  var inventorySourceCounts = {};
  var verifiedRows = [];
  var CATALOGUE_INITIAL_LIMIT = 18;
  var INVENTORY_PAGE_SIZE = 18;
  var MAX_SEARCH_RESULTS = 6;
  var inventoryExpanded = false;
  var searchExpanded = false;
  var lastSearchQuery = "";
  var lastSearchMatches = [];
  var lastStrictMatchCount = 0;
  var guidedControls = ["researchGuidedBudget", "researchGuidedPriority", "researchGuidedRam", "researchGuidedStorage", "researchGuidedExclude"].map(function (id) { return document.getElementById(id); });
  var guidedScope = document.getElementById("researchGuidedScope");
  var appliedFilters = document.getElementById("researchAppliedFilters");
  var clearSearchButton = document.getElementById("researchClearSearch");
  var guidedApply = document.getElementById("researchGuidedApply");
  var guidedStatus = document.getElementById("researchGuidedStatus");
  var comparisonSelection = [];
  var comparePanel = document.getElementById("mobileResearchCompare");
  var savedShortlistButton = document.getElementById("researchSavedShortlist");
  var SAVED_SHORTLIST_KEY = "cw-saved-phone-shortlist-v1";
  // Only model identifiers are saved on-device; no queries, prices or API observations.
  function persistShortlist() {
    try {
      var keys = comparisonSelection.map(function (item) { return item.card.model_key; });
      if (keys.length) window.localStorage.setItem(SAVED_SHORTLIST_KEY, JSON.stringify(keys));
      else window.localStorage.removeItem(SAVED_SHORTLIST_KEY);
    } catch (_) { /* Storage may be disabled; comparing still works. */ }
  }
  function restoreShortlist() {
    var stored;
    try { stored = JSON.parse(window.localStorage.getItem(SAVED_SHORTLIST_KEY) || "[]"); }
    catch (_) { stored = []; }
    if (!Array.isArray(stored)) stored = [];
    var seen = new Set();
    comparisonSelection = stored.slice(0, 3).map(function (key) {
      if (typeof key !== "string" || seen.has(key)) return null;
      var card = inventoryCards.find(function (item) { return item.model_key === key; });
      if (!card) return null;
      seen.add(key);
      return {card: card, rows: inventoryRowsForCard(card)};
    }).filter(Boolean);
    renderSelectedComparison();
    if (stored.length && comparisonSelection.length !== stored.length) persistShortlist();
  }
  function researchIntent(query) {
    var value = String(query || "").toLowerCase();
    if (/under\s*\d|₹|budget|price|कीमत/.test(value)) return "budget";
    if (/compare|\bvs\b|versus|और|तुलना/.test(value)) return "compare";
    if (/camera|कैमरा/.test(value)) return "camera";
    if (/battery|बैटरी/.test(value)) return "battery";
    if (/gaming|गेमिंग/.test(value)) return "gaming";
    if (/ram|storage|memory|रैम|स्टोरेज/.test(value)) return "memory_variant";
    return "model_or_general";
  }
  function trackResearchEvent(name, params) {
    try {
      if (typeof window.gtag === "function") window.gtag("event", name, params || {});
    } catch (_) { /* Analytics must never interrupt research. */ }
  }
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
    var amazon = /^https:\/\/(?:www\.)?amazon\.in(?:[/?#]|$)/i.test(String(url));
    if (amazon) { var parsed = new URL(url); parsed.searchParams.set("tag", "guru07cc-21"); url = parsed.href; }
    return '<a class="mobile-research-link" href="' + escapeHtml(url) + '" target="_blank" rel="' + (amazon ? 'sponsored nofollow noopener noreferrer' : 'noopener noreferrer') + '">' + escapeHtml(label) + " ↗</a>";
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
      return inventoryByKey.get(key);
    }).filter(Boolean);
    var frozen = (card.frozen_variant_ids || []).map(function (id) {
      return verifiedById.get(id);
    }).filter(Boolean);
    var rows = discovery.concat(frozen);
    (card.verified_india_variants || []).forEach(function (variant) {
      if (rows.some(function (row) { return row.ram_gb === variant.ram_gb && row.storage_gb === variant.storage_gb; })) return;
      rows.push({
        ram_gb: variant.ram_gb, storage_gb: variant.storage_gb,
        status: "PARTIALLY_VERIFIED",
        variant_text: variant.ram_gb + "GB RAM / " + variant.storage_gb + "GB storage",
        source_urls: [variant.source_url]
      });
    });
    return rows;
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
      rows.some(function (row) { return (!ram || String(row.ram_gb || "") === ram) && (!storage || String(row.storage_gb || "") === storage); }) &&
      (!status || rows.some(function (row) { return inventoryVariantStatus(row) === status; }));
  }

  function researchPhoneImage(card) {
    var name = displayPhoneName(card);
    var trigger = '<button type="button" class="research-photo-open" data-research-detail="' +
      escapeHtml(card.model_key) + '" aria-label="View specifications and retailer choices for ' + escapeHtml(name) + '" aria-expanded="false">';
    var photo = card.image_status === "VERIFIED_MATCH" && card.photo;
    if (photo) {
      return '<figure class="research-phone-photo">' + trigger + '<img src="' + escapeHtml(photo.url) +
        '" width="' + escapeHtml(photo.width) + '" height="' + escapeHtml(photo.height) +
        '" loading="lazy" decoding="async" alt="' + escapeHtml(name) +
        '"></button><figcaption><span class="photo-tap-hint">Tap photo to see retailer choices</span>Model photo: <a href="' + escapeHtml(photo.source) + '">' +
        (photo.title ? escapeHtml(photo.title) + " by " : "") + escapeHtml(photo.author) + '</a> · <a href="' + escapeHtml(photo.license_url) +
        '">' + escapeHtml(photo.license) + '</a> · resized</figcaption></figure>';
    }
    // Original, model-labelled generic artwork, never a fake manufacturer photo.
    // This asset is generated and owned by this site; exact model photographs
    // require a commercial-use permission record before publication.
    if (card.market_intake === true && typeof card.research_art_url === "string" &&
        /^\/assets\/new-mobile-art\/[a-z0-9-]+\.svg$/.test(card.research_art_url)) {
      return '<button type="button" class="research-photo-open research-phone-visual" data-research-detail="' +
        escapeHtml(card.model_key) + '" aria-label="View retailer choices for ' + escapeHtml(name) +
        '" aria-expanded="false"><img src="' + escapeHtml(card.research_art_url) +
        '" width="540" height="430" loading="lazy" decoding="async" alt="Generic illustrated smartphone, not an actual photo of ' +
        escapeHtml(name) + '"></button><p class="research-illustration-label">Original generic artwork · NOT an actual model photo · Tap to see retailers</p>';
    }
    // An illustration is not a verified model photograph. The same accessible
    // control opens existing details without claiming an exact product image.
    return '<button type="button" class="research-photo-open research-phone-visual" data-research-detail="' +
      escapeHtml(card.model_key) + '" aria-label="View specifications and retailer choices for ' + escapeHtml(name) +
      '" aria-expanded="false"><img src="/assets/phone-study.svg" width="600" height="540" alt="" loading="lazy"><span>' +
      escapeHtml(card.brand) + ' / PHONE RESEARCH</span></button><p class="research-illustration-label">Illustration · not a product photo · Tap to see retailers</p>';
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
      var label = String(specificationLabel(key, item)).replace(/_/g, " ");
      var value = specValue(key, item);
      if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
    });
    frozenRows.forEach(function (row) {
      Object.keys(row.specifications || {}).forEach(function (key) {
        var item = row.specifications[key] || {};
        var label = String(specificationLabel(key, item)).replace(/_/g, " ");
        var value = specValue(key, item);
        if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
      });
    });
    var frozenSpecs = Object.keys(specSet).map(function (entry) {
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
      '<div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status inventory-status-' + escapeHtml(statusLabel.toLowerCase()) + '">' + escapeHtml(statusLabel) + '</span></div>' +
      researchPhoneImage(card) + '<h3>' +
       (card.market_intake && /^\/phones\/[a-z0-9-]+\/(?:[a-z0-9-]+\/)?$/.test(String(card.detail_url || "")) ?
        '<a class="research-model-name-link" href="' + escapeHtml(card.detail_url) + '">' + escapeHtml(displayPhoneName(card)) + '</a>' :
        escapeHtml(displayPhoneName(card))) + '</h3>' + launch +
      (card.market_intake ? '<p class="mobile-research-gate"><strong>Additional India research model:</strong> original illustration, not exact model photograph; fresh exact-SKU price unavailable. ' + link(card.manufacturer_page || (card.source_urls || [])[0], "Manufacturer source") + '</p>' : '') +
      '<p class="mobile-research-variant">' + escapeHtml(counts || "Model research reference") + '</p>' +
      '<ul class="mobile-research-variant-list">' + (variantItems || "<li>Variant details are not specified in the source universe.</li>") + '</ul>' +
      '<p class="mobile-research-inventory-fields"><strong>Verified fields:</strong> ' + escapeHtml(fields) + '</p>' +
      '<details class="mobile-research-model-details"><summary>View specifications / details</summary>' + details + '</details>' +
      '<p class="mobile-research-inventory-reason">' + (card.market_intake ?
       'New India market research intake, separate from the 232 original catalogue cards. Exact retailer identity, prices, stock and image rights are unverified.' :
       'Model card groups source-backed discovery records and frozen exact variants. It does not certify availability or purchase eligibility.') + '</p>' +
      '<div class="mobile-research-sources">' + sources + '</div>' + retailerResearchLinks(card) +
      '<p class="mobile-research-gate">Research only · no price · no stock · no purchase action</p>' +
      '</div></article>';
  }

  function renderInventory() {
    if (!inventoryGrid) return;
    var filtered = inventoryCards.filter(inventoryMatches);
    // New manufacturer-linked phones were formerly hidden after 232 core
    // entries: bring them to the top without changing research ranking.
    filtered = filtered.slice().sort(function (a, b) {
      return Number(Boolean(b.market_intake)) - Number(Boolean(a.market_intake)) ||
        String(b.research_checked_at || "").localeCompare(String(a.research_checked_at || ""));
    });
    var matchingVariants = filtered.reduce(function (count, card) { return count + inventoryRowsForCard(card).length; }, 0);
    var isUnfiltered = !(inventoryQuery && inventoryQuery.value) && !(inventoryBrand && inventoryBrand.value) && !(inventoryRam && inventoryRam.value) && !(inventoryStorage && inventoryStorage.value) && !(inventoryStatus && inventoryStatus.value);
    if (inventoryCount) {
      inventoryCount.textContent = isUnfiltered && inventorySourceCounts.visible_model_cards ?
        inventorySourceCounts.visible_model_cards + " original catalogue models" + (marketIntakeCount ? " + " + marketIntakeCount + " new market research models" : "") + " · " + (inventorySourceCounts.deduplicated_discovery_records || inventoryRows.length) + " original research records · " + (inventorySourceCounts.frozen_verified_variants || verifiedRows.length) + " frozen exact variants" :
        filtered.length + " catalogue entries · " + matchingVariants + " matching research/frozen variants";
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
    // Import only the eight source-reviewed missing market identities.
    // They remain separate from the original 232-card registry, ratings and offers.
    var coreFetch = fetch("/data/mobile_research_catalogue.json?v=licensed-photos-20261117", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("research catalogue unavailable");
        return response.json();
      });
    var marketFetch = fetch("/data/india_sales_eight_research.json?v=20261118", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("market intake unavailable");
        return response.json();
      }).catch(function () { return null; });
    var recentFetch = fetch("/data/india_recent_manufacturer_research.json?v=20261118d", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("recent phone research unavailable");
        return response.json();
      }).catch(function () { return null; });
    Promise.all([coreFetch, marketFetch, recentFetch])
      .then(function (results) {
        var payload = results[0], intake = results[1], recent = results[2];
        inventoryLoadFailed = false;
        inventoryRows = Array.isArray(payload.records) ? payload.records : [];
        inventoryByKey = new Map(inventoryRows.map(function (row) { return [row.record_key, row]; }));
        inventoryCards = Array.isArray(payload.model_cards) ? payload.model_cards : [];
        inventorySourceCounts = payload.source_counts || {};
        marketIntakeCount = 0;
        if (intake && intake.mode === "EIGHT_SOURCE_REVIEWED_MARKET_ADDITIONS_NO_LIVE_OFFERS" &&
            intake.core_model_count_unchanged === 232 &&
            Array.isArray(intake.model_cards) && intake.model_cards.length === 8 &&
            Array.isArray(intake.records) && intake.records.length === 8) {
          var known = new Set(inventoryCards.map(function (card) { return card.model_key; }));
          var imported = intake.model_cards.every(function (card) {
            return card.market_intake === true && card.status === "RESEARCH_ONLY" &&
              card.image_status === "PLACEHOLDER" && !card.photo && !known.has(card.model_key) &&
              Array.isArray(card.verified_retailer_links) && !card.verified_retailer_links.length;
          });
          if (imported) {
            intake.records.forEach(function (row) { inventoryByKey.set(row.record_key, row); inventoryRows.push(row); });
            inventoryCards = inventoryCards.concat(intake.model_cards);
            marketIntakeCount = intake.model_cards.length;
          }
        }
        // Strictly separate manufacturer-source discovery from canonical phones
        // and exact retail SKUs. Ignore incomplete or conflicting data entirely.
        if (recent && recent.mode === "RECENT_INDIA_MANUFACTURER_MODELS_RESEARCH_ONLY" &&
            recent.core_model_count_unchanged === 232 &&
            Array.isArray(recent.model_cards) && recent.model_cards.length === 13 &&
            Array.isArray(recent.records) && recent.records.length === 13) {
          var identifiers = new Set(inventoryCards.map(function (card) { return card.model_key; }));
          var recordIds = new Set(inventoryRows.map(function (row) { return row.record_key; }));
          var safeRecent = recent.model_cards.every(function (card) {
            return card.market_intake === true && card.status === "RESEARCH_ONLY" &&
              card.image_status === "PLACEHOLDER" && !card.photo &&
              !identifiers.has(card.model_key) &&
              Array.isArray(card.discovery_record_keys) && card.discovery_record_keys.length === 1 &&
              Array.isArray(card.verified_retailer_links) && !card.verified_retailer_links.length &&
              Array.isArray(card.frozen_variant_ids) && !card.frozen_variant_ids.length &&
              card.specifications && Object.values(card.specifications).every(function (field) {
                return field && typeof field.value === "string" && field.value.trim() &&
                  field.source_url === card.manufacturer_page;
              });
          }) && recent.records.every(function (row) {
            return row.status === "RESEARCH_ONLY" && !recordIds.has(row.record_key);
          }) && new Set(recent.model_cards.map(function (card) { return card.model_key; })).size === recent.model_cards.length &&
              new Set(recent.records.map(function (row) { return row.record_key; })).size === recent.records.length;
          if (safeRecent) {
            recent.records.forEach(function (row) { inventoryByKey.set(row.record_key, row); inventoryRows.push(row); });
            inventoryCards = inventoryCards.concat(recent.model_cards);
            marketIntakeCount += recent.model_cards.length;
          }
        }
        refreshInventoryControls();
        restoreShortlist();
        renderNewNoteworthy();
        handleResearchHash();
        var initialQuery = lastSearchQuery || new URLSearchParams(window.location.search || "").get("q");
        if (initialQuery) submitResearch(initialQuery);
      })
      .catch(function () {
        inventoryLoadFailed = true;
        if (researchSearchStatus) researchSearchStatus.textContent = "Saved smartphone research is temporarily unavailable. Use the Standard Buying Guide below.";
        if (researchResults) { researchResults.hidden = false; researchResults.innerHTML = researchGuideFallback(); }
        if (inventoryCount) inventoryCount.textContent = "Research catalogue unavailable";
        inventoryGrid.innerHTML = "<p>Existing research records are currently unavailable.</p>" + researchGuideFallback();
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
      return '<li><span>' + escapeHtml(specificationLabel(key, item)) + '</span><strong>' + escapeHtml(specValue(key, item)) + '</strong></li>';
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


  function researchConstraints(query) {
    var text = String(query || "").toLowerCase().replace(/[०-९]/g, function (d) { return String("०१२३४५६७८९".indexOf(d)); }).replace(/,/g, "");
    text = text.replace(/सैमसंग/g, "samsung").replace(/आईफोन/g, "iphone").replace(/रेडमी/g, "redmi").replace(/वनप्लस/g, "oneplus");
    var amount = "([0-9]+(?:\\.[0-9]+)?)\\s*(k|thousand|hazar|hazaar|हजार|हज़ार|lakh|lac|लाख)?";
    function value(n, unit) { return Number(n) * (/^(k|thousand|hazar|hazaar|हजार|हज़ार)$/.test(unit || "") ? 1000 : /^(lakh|lac|लाख)$/.test(unit || "") ? 100000 : 1); }
    var nearbyBudget = /\bnearby\s+(?:band|budget)\b/i.test(text);
    text = text.replace(/\bnearby\s+(?:band|budget)\b/gi, " ");
    var fullBudget = /\bfull\s+budget\b|पूरे\s*बजट/i.test(text);
    text = text.replace(/\bfull\s+budget\b|पूरे\s*बजट/gi, " ");
    // "Top 3" controls presentation only; the numeral is not a phone-model token.
    text = text.replace(/\btop\s*3\b/gi, " ");
    var budget = null, lower = null, inclusive = false;
    var between = text.match(new RegExp("(?:between|from)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount + "\\s*(?:and|to|-)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount));
    if (between) { lower = value(between[1], between[2] || between[4]); budget = value(between[3], between[4]); inclusive = true; text = text.replace(between[0], " "); }
    else {
      var prefix = text.match(new RegExp("(?:under|below|within|upto|up to|budget(?: of)?)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount));
      var suffix = text.match(new RegExp("(?:rs\\.?|inr|₹)?\\s*" + amount + "\\s*(?:rupees|रुपये|रुपए)?\\s*(?:ke\\s*)?(?:andar|se kam|के\\s*अंदर|के\\s*नीचे|से\\s*कम|तक)"));
      var currency = text.match(new RegExp("(?:₹|rs\\.?|inr)\\s*" + amount));
      var m = prefix || suffix || currency;
      if (m) { budget = value(m[1], m[2]); inclusive = /within|upto|up to|तक/.test(m[0]); text = text.replace(m[0], " "); }
    }
    // Budget shortcuts show the immediately preceding five-thousand-rupee
    // reference band. The explicit "full budget" option is the opt-in path
    // for every documented cheaper candidate below the cap.
    if (budget != null && lower == null) {
      lower = !fullBudget ? Math.max(0, budget - 5000) : 0;
    }
    var ram = null, storage = null;
    text = text.replace(/\b(\d{1,2})\s*\/\s*(\d{2,4})\b/g, function (_, r, t) { ram = Number(r); storage = Number(t); return " "; });
    text = text.replace(/\b(\d+(?:\.\d+)?)\s*(gb|tb)\s*(?:(?:physical|internal)\s+)?(ram|storage|rom)?\b/g, function (_, n, unit, type) {
      var size = Number(n) * (unit === "tb" ? 1024 : 1);
      if (type === "ram" || (!type && size <= 24)) ram = size; else storage = size;
      return " ";
    });
    var minimumBattery = null, minimumRefresh = null;
    text = text.replace(/\b(\d{3,5})\s*mah\b/g, function (_, n) { minimumBattery = Number(n); return " battery "; });
    text = text.replace(/\b(\d{2,3})\s*hz\b/g, function (_, n) { minimumRefresh = Number(n); return " display "; });
    var need5g = /\b5g\b/.test(text); text = text.replace(/\b5g\b/g, " ");
    var needOis = /\bois\b/.test(text); text = text.replace(/\bois\b/g, " camera ");
    return { text: normalizeResearch(text), budget: budget, lower: lower, inclusive: inclusive, ram: ram, storage: storage, minimumBattery: minimumBattery, minimumRefresh: minimumRefresh, need5g: need5g, needOis: needOis };
  }


  function researchRowsFor(card, c) {
    var rows;
    if (c.budget != null) {
      var ref = card.research_budget_reference;
      if (!validResearchBudgetReference(ref)) return [];
      if (c.inclusive ? ref.reference_price_inr > c.budget : ref.reference_price_inr >= c.budget) return [];
      if (c.lower != null && ref.reference_price_inr < c.lower) return [];
      rows = [{ ram_gb: ref.ram_gb, storage_gb: ref.storage_gb, variant_text: (ref.ram_gb == null ? "RAM not officially specified" : ref.ram_gb + "GB RAM") + " / " + ref.storage_gb + "GB storage", research_reference: true }];
    } else {
      rows = inventoryRowsForCard(card);
    }
    return rows.filter(function (row) { return (c.ram == null || Number(row.ram_gb) === c.ram) && (c.storage == null || Number(row.storage_gb) === c.storage); });
  }

  function validResearchBudgetReference(ref) {
    if (!ref || ref.live_offer !== false || ref.ranking_weight !== 0) return false;
    if (typeof ref.reference_price_inr !== "number" || !Number.isFinite(ref.reference_price_inr) || ref.reference_price_inr <= 0) return false;
    if (!ref.checked_at || !Number.isFinite(Date.parse(String(ref.checked_at)))) return false;
    if (/(OUT[\s._-]*OF[\s._-]*STOCK|UNAVAILABLE|DISCONTINUED)/i.test(String(ref.stock_indication || ""))) return false;
    return true;
  }

  function excludedBrand(query) {
    // Common Hinglish negation: "vivo nahi chahiye".
    var negative = String(query || "").match(/\b([a-z][a-z0-9/&-]*)\s+(?:nahi|nahin)\s+chahiye\b/i);
    if (negative) return normalizeResearch(negative[1]);
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
      [/(?:student|study|college|school|स्टूडेंट|पढ़ाई)/, ["battery_mah_typical", "operating_system", "security_update_policy", "display_type", "display_refresh_max_hz"]],
      [/software|android|update|support|सॉफ्टवेयर/, ["operating_system", "launch_android", "os_upgrade_generations", "security_update_policy", "security_support_years"]],
      [/display|screen|डिस्प्ले/, ["display_type", "display_inches", "display_resolution", "display_refresh_max_hz"]],
      [/build|reliability|durability/, ["ip_rating", "durability"]]
    ];
    groups.forEach(function (group) { if (group[0].test(text)) keys = keys.concat(group[1]); });
    return Array.from(new Set(keys));
  }

  function researchSpecKeys(card, rows) {
    var keys = Object.keys(card.specifications || {});
    (rows || []).forEach(function (row) { keys = keys.concat(Object.keys(row.specifications || {})); });
    return keys;
  }


  function findResearchMatches(query, ignoreBudgetForUnpricedResearch) {
    var c = researchConstraints(query), text = c.text;
    // Remember the original budget intent before temporarily relaxing ONLY
    // its price-reference constraint for the second evidence lane.
    var priceUnknownBudgetResearch = ignoreBudgetForUnpricedResearch === true && c.budget != null;
    if (ignoreBudgetForUnpricedResearch === true) { c.budget = null; c.lower = null; }
    var excluded = excludedBrand(text), featureKeys = researchFeatureKeys(text);
    var stop = /^(best|good|phone|phones|mobile|mobiles|smartphone|smartphones|under|below|within|price|in|the|and|with|ram|storage|camera|battery|gaming|game|student|study|college|school|software|support|display|screen|build|reliability|durability|android|update|updates|ko|ke|ka|ki|bina|chhodkar|chhod|mujhe|mujhko|chahiye|batao|dikhao|achha|acha|accha|wala|wali|mein|me|se|kam|tak|rs|inr|rupees|minimum|least|at|above|over|more|than|का|की|के|में|मुझे|चाहिए|बताओ|दिखाओ|अच्छा|अच्छे|वाला|वाले|फोन|मोबाइल|कैमरा|बैटरी|गेमिंग|स्टूडेंट|पढ़ाई|डिस्प्ले|छोड़कर|छोड़|हटाकर|बिना|exclude|excluding|without|except|no)$/;
    var tokens = text.split(" ").filter(function (token) { return token && !stop.test(token) && token !== excluded; });
    var aliases = { "सैमसंग": "samsung", "आईफोन": "iphone", "रेडमी": "redmi", "पोको": "poco", "वनप्लस": "oneplus" };
    tokens = tokens.map(function (token) { return aliases[token] || token; });
    if (!tokens.length && !featureKeys.length && !excluded && c.budget == null && c.ram == null && c.storage == null && !c.need5g && !priceUnknownBudgetResearch) return [];
    // Natural-language instruction words are not product model tokens.
    // Keep model suffixes (Pro/Plus/Max), RAM, storage and hard gates intact.
    var queryNoise = new Set([
      "exact", "model", "models", "priority", "priorities", "prefer", "preferred",
      "recommend", "recommendation", "recommended", "suggest", "suggestion",
      "please", "find", "show", "give", "need", "looking", "for",
      "new", "latest", "best", "top", "quality", "overall", "performance",
      "phone", "phones", "smartphone", "smartphones", "mobile", "mobiles",
      "price", "budget", "range", "india", "indian", "available",
      "as", "is", "it", "do", "does", "the", "what", "which", "that",
      "ke", "liye", "pe", "par", "ko", "se", "ka", "ki",
      "hai", "hain", "nahi", "nahin", "chahiye", "chahie", "mujhe",
      "good", "better", "worth", "cheap", "sasta", "sasti",
      "student", "study", "college", "school", "स्टूडेंट", "पढ़ाई",
      "compromise", "without", "some", "any", "only", "just"
    ]);
    tokens = tokens.filter(function (token) { return !queryNoise.has(token); });
    var matches = [];
    // In a budget/physical-memory request, an exact model name must not
    // be replaced with a priced Pro/Plus/Max/e sibling. Keep broad identity
    // discovery ("iPhone 16", "Lava Bold N2") unchanged without hard filters.
    var strictModelIdentity = c.budget != null || priceUnknownBudgetResearch ||
      c.ram != null || c.storage != null;
    var exactCard = strictModelIdentity && text.split(" ").length >= 2 && inventoryCards.find(function (card) {
      return normalizeResearch(displayPhoneName(card).replace(/\b5g\b/ig, "")) === text ||
        normalizeResearch(displayPhoneName(card)) === text;
    });
    (exactCard ? [exactCard] : inventoryCards).forEach(function (card) {
      if (excluded && normalizeResearch(card.brand).indexOf(excluded) >= 0) return;
      var rows = researchRowsFor(card, c);
      if (!rows.length) return;
      var specs = card.specifications || {};
      function spec(key) { return specs[key] && specs[key].value; }
      if (c.minimumBattery != null && !(Number(spec("battery_mah_typical")) >= c.minimumBattery)) return;
      if (c.minimumRefresh != null && !(Number(spec("display_refresh_max_hz")) >= c.minimumRefresh)) return;
      if (c.needOis && !/^(yes|true|supported)$/i.test(String(spec("ois") || ""))) return;
      if (c.need5g && normalizeResearch((card.brand + " " + card.model).replace(/\b5g\b/ig, "")) !== text) {
        // An exact model-name lookup is an identity search, not proof of 5G support.
        // Explicit category searches still require manufacturer-sourced network evidence.
        var networkEvidence = specs.network_support;
        var networkValue = String(networkEvidence && networkEvidence.value || "");
        var networkSource = String(networkEvidence && networkEvidence.source_url || "");
        var manufacturerDomains = /^(?:[a-z0-9-]+\.)*(?:samsung\.com|apple\.com|mi\.com|xiaomi\.com|oneplus\.com|oneplus\.in|oppo\.com|vivo\.com|realme\.com|motorola\.com|motorola\.in|nothing\.tech|google\.com|poco\.in|iqoo\.com|honor\.com|infinixmobility\.com|tecno-mobile\.com|hmd\.com|nokia\.com)$/i;
        var sourceHost = /^https:\/\/([^\/:?#]+)/i.exec(networkSource);
        var sourcedByManufacturer = !!(sourceHost && manufacturerDomains.test(sourceHost[1]));
        if (!sourcedByManufacturer || !/(?:\b5g\b|\bnr\b|n(?:1|3|5|8|28|40|41|77|78|79)\b)/i.test(networkValue)) return;
      }
      if (tokens.length) {
        var hayTokens = normalizeResearch(card.brand + " " + card.model).split(" ");
        if (!tokens.every(function (token) { return hayTokens.indexOf(token) >= 0; })) return;
      }
      if (featureKeys.length) {
        var keys = researchSpecKeys(card, rows);
        if (!featureKeys.some(function (key) { return keys.indexOf(key) >= 0; })) return;
      }
      matches.push({card: card, rows: rows});
    });
    return sortResearchMatches(matches, query);
  }



  function displayPhoneName(card) {
    var brand = String(card.brand || "");
    if (brand.toLowerCase() === "samsung") brand = "Samsung";
    if (normalizeResearch(brand) === "xiaomi redmi") brand = "Redmi";
    var model = String(card.model || "");
    if (normalizeResearch(model).indexOf(normalizeResearch(brand) + " ") === 0) return model;
    return brand + " " + model;
  }

  function researchGroupKey(card) {
    // Display grouping only. No source row, price or variant is transferred.
    var name = normalizeResearch(displayPhoneName(card))
      .replace(/\s+(?:mobile\s+)?(?:moonlight|sapphire|frost|thunder|light|bahama|violet|velvet)(?:\s+(?:silver|black|blue))?$/, "")
      .replace(/\s+smartphone$/, "")
      .replace(/\s+\d+\s*gb(?:\s+ram)?/g, "").trim();
    // These spelling aliases share the manufacturer's exact specification URL.
    var aliases = {"vivo t5x": "vivo t5x 5g", "oppo k13 turbo": "oppo k13 turbo 5g"};
    return aliases[name] || name;
  }

  function groupResearchMatches(matches) {
    var seen = {}, result = [];
    matches.forEach(function (item) {
      var key = researchGroupKey(item.card);
      if (seen[key]) { seen[key].group_size += 1; return; }
      var copy = {card: item.card, rows: item.rows, group_size: 1};
      seen[key] = copy; result.push(copy);
    });
    return result;
  }

  function specificationLabel(key, item) {
    var value = String(item && item.value || "");
    if (key === "chipset" && /ghz/i.test(value) && !/snapdragon|exynos|dimensity|bionic|tensor|mediatek|unisoc/i.test(value)) return "CPU clock (chipset name unconfirmed)";
    if (/display_type/.test(key) && /colou?r depth|16m/i.test(value)) return "Display colour depth";
    return item.label || TECHNICAL_FIELD_LABELS[key] || key.replace(/_/g, " ");
  }

  function compactSpecRows(card, query) {
    var specs = card.specifications || {};
    var groups = [
      ["chipset"], ["display_type", "display_type_description"], ["display_refresh_max_hz", "display_refresh_description"],
      ["rear_main_mp", "rear_camera_system"], ["ois"], ["battery_mah_typical", "battery_capacity_description", "battery_and_charging"],
      ["wired_charging_max_w", "charging_description"], ["security_support_years", "security_update_policy", "operating_system"],
      ["display_resolution", "display_resolution_description"], ["gpu"], ["ip_rating", "durability"]
    ];
    var priorities = researchFeatureKeys(query), keys = [];
    groups.forEach(function (group) { var key = group.find(function (k) { return specs[k] && specs[k].value !== "" && specs[k].value != null; }); if (key) keys.push(key); });
    keys.sort(function (a, b) { return (priorities.indexOf(a) < 0 ? 100 : priorities.indexOf(a)) - (priorities.indexOf(b) < 0 ? 100 : priorities.indexOf(b)); });
    return keys.slice(0, 6).map(function (key) { return {key:key, label:specificationLabel(key, specs[key]), value:specValue(key, specs[key])}; });
  }

  function documentedContext(card, query) {
    var specs = card.specifications || {};
    var text = normalizeResearch(query), fact = "Compare these documented specifications with your everyday needs.";
    var caution = "Current price, exact listing and delivery need retailer confirmation.";
    if (/camera|कैमरा/.test(text)) {
      var ois = specs.ois && String(specs.ois.value);
      fact = /^(yes|true|supported)$/i.test(ois || "") ? "Optical image stabilization (OIS) is listed in the source." : "Optical image stabilization is not confirmed in this record.";
      caution = "Megapixels alone do not establish photo quality. Check camera samples and independent tests.";
    } else if (/battery|बैटरी/.test(text)) {
      var battery = specs.battery_mah_typical;
      fact = battery ? "Listed battery capacity: " + specValue("battery_mah_typical", battery) + "." : "Battery capacity needs confirmation from the source.";
      caution = "Capacity is not measured battery life. Usage, signal and charging tests also matter.";
    } else if (/gaming|game|गेमिंग/.test(text)) {
      fact = "Processor and GPU specifications are shown where documented.";
      caution = "Chipset names alone do not establish sustained FPS, heating or gaming endurance.";
    } else if (/build|reliability|durability/.test(text)) {
      fact = specs.ip_rating ? "Documented ingress-protection rating: " + specs.ip_rating.value + "." : "An ingress-protection rating is not confirmed in this record.";
      caution = "An IP rating does not establish drop resistance or long-term reliability. Check warranty conditions and repair support.";
    } else if (/software|support|update|android/.test(text)) {
      fact = "Check the documented operating system and update policy below.";
      caution = "An update promise is not the remaining support period. Confirm launch and support-end dates.";
    }
    var checks = [];
    function hasEvidence(key) {
      var item = specs[key];
      return !!(item && item.value != null && String(item.value).trim() !== "" &&
        /^https:\/\/[^\s<>"']+$/i.test(String(item.source_url || "")));
    }
    if (/camera|कैमरा/.test(text)) {
      checks = [["OIS source", ["ois"]], ["Camera hardware", ["rear_main_mp", "rear_camera_system"]]];
    } else if (/battery|बैटरी/.test(text)) {
      checks = [["Battery capacity", ["battery_mah_typical", "battery_capacity_description"]], ["Charging", ["wired_charging_max_w", "charging_description"]]];
    } else if (/gaming|game|गेमिंग/.test(text)) {
      checks = [["Chipset", ["chipset"]], ["GPU", ["gpu"]]];
    } else if (/software|support|update|android/.test(text)) {
      checks = [["Operating system", ["operating_system"]], ["Update policy", ["security_update_policy", "security_support_years"]]];
    } else if (/build|reliability|durability/.test(text)) {
      checks = [["Ingress protection", ["ip_rating"]]];
    }
    var checklist = checks.length ? '<p><strong>Decision evidence checklist</strong> ' +
      checks.map(function (entry) {
        return escapeHtml(entry[0]) + ': ' +
          (entry[1].some(hasEvidence) ? 'Source linked' : 'Not source-confirmed');
      }).join(' · ') + '</p>' : '';
    return '<div class="research-context"><p><strong>What to consider</strong> ' + escapeHtml(fact) +
      '</p><p><strong>Before choosing</strong> ' + escapeHtml(caution) +
      '</p>' + checklist + '<p><small>Research evidence is not a measured performance verdict.</small></p></div>';
  }

  function retailerResearchLinks(card) {
    // Reuse the existing exact-identity and retailer-search records; never
    // transform a research search into a verified buy/stock/price CTA.
    var exact = card.verified_retailer_links || [];
    var searches = card.retailer_search_links || [];
    var stores = [
      {id: "flipkart", name: "Flipkart", hosts: ["flipkart.com", "www.flipkart.com"]},
      {id: "amazon", name: "Amazon", hosts: ["amazon.in", "www.amazon.in"]},
      {id: "croma", name: "Croma", hosts: ["croma.com", "www.croma.com"]}
    ];
    return '<div class="mobile-research-sources retailer-search-links" aria-label="Retailer choices">' +
      stores.map(function (store) {
        var verified = exact.find(function (item) { return String(item.retailer || "").toLowerCase() === store.id; });
        var fallback = searches.find(function (item) { return String(item.retailer || "").toLowerCase() === store.id; });
        var item = verified || fallback;
        if (item) {
          try {
            var parsed = new URL(String(item.url || ""));
            if (parsed.protocol === "https:" && store.hosts.indexOf(parsed.hostname.toLowerCase()) >= 0) {
              var label = verified ? "View exact " + store.name + " listing" :
                (store.id === "croma" ? "Search Croma for this model" : "Search " + store.name);
              return link(item.url, label);
            }
          } catch (error) { /* Invalid links remain unavailable, not clickable. */ }
        }
        return '<span class="retailer-choice-unavailable" aria-disabled="true">' +
          escapeHtml(store.name) + '<small>Link unavailable</small></span>';
      }).join(" ") + '</div>' +
      '<div class="api-price-observations"><button type="button" data-price-observations="' +
      escapeHtml(card.model_key) + '" aria-expanded="false">View saved price &amp; stock checks</button>' +
      '<div data-api-price-panel hidden aria-live="polite"></div></div>';
  }

  function independentTestContext(card) {
    var tests = card.independent_tests || [];
    if (!tests.length) return "";
    return '<details class="research-independent-tests"><summary>Independent lab tests (' + tests.length + ')</summary><p>' + escapeHtml(card.independent_test_limitation) + '</p>' + tests.map(function (test) {
      return '<div class="research-lab-measurement"><p><strong>' + escapeHtml(test.label) + ': ' + escapeHtml(test.value) + ' ' + escapeHtml(test.unit) + '</strong></p><p>Tested: ' + escapeHtml(test.tested_unit) + '</p><p>' + escapeHtml(test.protocol) + ' · Version: ' + escapeHtml(test.test_version || 'not reported') + ' · ' + escapeHtml(test.conditions) + '</p><p>' + link(test.source_url, test.source_name + ' test source') + ' · Source checked: ' + escapeHtml(test.checked_at) + ' · Measurement date: ' + escapeHtml(test.observed_at || 'not separately reported') + '</p></div>';
    }).join('') + '<p>Source-specific measurements; excluded from Best 3 scoring. Missing tests on other phones do not mean worse performance.</p></details>';
  }

  function renderResearchResultCard(card, rows, groupSize) {
    var variants = Array.from(new Set(rows.map(function (row) { return (row.ram_gb != null ? row.ram_gb + "GB RAM" : "RAM not specified") + " · " + (row.storage_gb != null ? row.storage_gb + "GB storage" : "storage not specified"); })));
    var facts = compactSpecRows(card, lastSearchQuery);
    var specs = facts.map(function (item) { var value = String(item.value); return '<li><span>' + escapeHtml(item.label) + '</span><strong title="' + escapeHtml(value) + '">' + escapeHtml(value.length > 160 ? value.slice(0, 157) + "…" : value) + '</strong></li>'; }).join("");
    var sourceItem = Object.values(card.specifications || {}).find(function (item) { return /^https:\/\//.test(item.source_url || ""); }) ||
      (card.market_intake && (card.manufacturer_page || (card.source_urls || [])[0]) ?
       {source_url: card.manufacturer_page || card.source_urls[0], checked_at: card.research_checked_at} : null);
    var status = card.market_intake ? "Manufacturer-linked model" :
      card.status === "OFFICIAL_VERIFIED" ? "Manufacturer evidence" :
      card.status === "PARTIALLY_VERIFIED" ? "Partial specifications" : "Needs verification";
    var selected = comparisonSelection.some(function (item) { return researchGroupKey(item.card) === researchGroupKey(card); });
    var launch = card.india_launch_date ? '<p class="mobile-research-launch">India launch: ' + escapeHtml(card.india_launch_date) + '</p>' : '';
    return '<article class="mobile-research-inventory-card mobile-research-result-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '"><div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status">' + escapeHtml(status) + '</span><span class="research-status">Research only</span></div>' +
      researchPhoneImage(card) + '<h3>' +
       (card.market_intake && /^\/phones\/[a-z0-9-]+\/(?:[a-z0-9-]+\/)?$/.test(String(card.detail_url || "")) ?
        '<a class="research-model-name-link" href="' + escapeHtml(card.detail_url) + '">' + escapeHtml(displayPhoneName(card)) + '</a>' :
        escapeHtml(displayPhoneName(card))) + '</h3>' + launch +
      (card.market_intake ? '<p class="mobile-research-gate">' +
        (card.recent_source_intake ? 'Recently added manufacturer-sourced India model' : 'India sales/shipments research addition') +
        ' · no verified current price, stock or exact retailer configuration.</p>' : '') +
      '<p class="mobile-research-variant">' + (variants.length ? 'Matching documented variant' + (variants.length > 1 ? "s" : "") + ': ' + escapeHtml(variants.join("; ")) : 'No exact variant recorded for this fallback record') + '</p>' +
      (groupSize > 1 ? '<p class="research-group-note">' + groupSize + ' matching catalogue entries grouped. Specifications below belong to the displayed record.</p>' : '') +
      (specs ? '<ul class="mobile-research-model-specs">' + specs + '</ul>' : '<p>Technical specifications are pending verification.</p>') + documentedContext(card, lastSearchQuery) + independentTestContext(card) +
      '<p class="research-source-note">' + (sourceItem ? link(sourceItem.source_url, "Specification source") : 'Specification source pending') + ' · Specification research snapshot: ' + escapeHtml(card.research_checked_at || sourceItem && (sourceItem.checked_at || sourceItem.checked_date) || 'date unavailable') + ' (not a live check)</p>' + (card.research_budget_reference ? '<p class="research-source-note">Budget filter uses a dated retailer observation: ' + escapeHtml(String(card.research_budget_reference.checked_at || 'date unavailable').match(/\d{4}-\d{2}-\d{2}/)?.[0] || String(card.research_budget_reference.checked_at || 'date unavailable')) + '. Current price and stock not verified.</p>' : '') +
      '<div class="research-card-actions"><button type="button" class="btn btn-ghost mobile-research-detail-button" data-research-detail="' + escapeHtml(card.model_key) + '">All specifications</button>' +
      '<button type="button" class="btn btn-ghost" data-research-compare="' + escapeHtml(card.model_key) + '" aria-pressed="' + selected + '">' + (selected ? 'Remove comparison' : 'Compare') + '</button></div>' + retailerResearchLinks(card) +
      (card.market_intake ? '<p class="mobile-research-gate"><strong>Price unavailable:</strong> no fresh authorized exact-SKU API price. Open the model specifications page for manufacturer evidence.</p>' : '') +
       '<p class="mobile-research-gate">Model-targeted retailer searches only, not exact-SKU purchase links. Exact listing links appear only where a retailer ID, model and physical variant were separately verified. Other retailer links are model searches. Confirm RAM/storage, current price, stock and delivery on retailer sites.</p></div></article>';
  }

  function renderSelectedComparison() {
    if (savedShortlistButton) {
      savedShortlistButton.hidden = comparisonSelection.length === 0;
      savedShortlistButton.textContent = "View saved shortlist (" + comparisonSelection.length + "/3)";
    }
    if (!comparePanel) return;
    comparePanel.hidden = comparisonSelection.length === 0;
    if (!comparisonSelection.length) { comparePanel.innerHTML = ""; return; }
    var fields = [
      ["Processor", ["chipset"]], ["GPU", ["gpu"]],
      ["Display", ["display_type", "display_type_description"]],
      ["Resolution", ["display_resolution", "display_resolution_description"]],
      ["Refresh rate", ["display_refresh_max_hz", "display_refresh_description"]],
      ["Main camera", ["rear_main_mp", "rear_camera_system"]],
      ["Ultrawide", ["rear_ultrawide_mp"]], ["Optical stabilization", ["ois"]],
      ["Battery", ["battery_mah_typical", "battery_capacity_description", "battery_and_charging"]],
      ["Charging", ["wired_charging_max_w", "charging_description"]],
      ["Software / updates", ["security_support_years", "security_update_policy", "operating_system"]],
      ["Water / dust resistance", ["ip_rating"]]
    ];
    function evidence(card, keys) {
      var key = keys.find(function (name) {
        var record = card.specifications && card.specifications[name];
        return record && record.value != null && String(record.value).trim() !== "";
      });
      if (!key) return { html: '<span class="research-missing-evidence">Not confirmed</span>', confirmed: false };
      var item = card.specifications[key];
      var text = (key === "chipset" && /ghz/i.test(String(item.value)) ? specificationLabel(key, item) + ": " : "") + specValue(key, item);
      var source = String(item.source_url || "");
      var link = /^https:\/\/[^\s<>"']+$/i.test(source)
        ? ' <a href="' + escapeHtml(source) + '" target="_blank" rel="noopener noreferrer" aria-label="Source for ' + escapeHtml(key) + '">Source</a>'
        : ' <small>(source link unavailable)</small>';
      return { html: escapeHtml(text) + link, confirmed: true };
    }
    var totals = comparisonSelection.map(function (selected) {
      return fields.filter(function (field) { return evidence(selected.card, field[1]).confirmed; }).length;
    });
    var header = comparisonSelection.map(function (selected, index) {
      var variants = selected.rows.filter(function (row) { return row.ram_gb != null || row.storage_gb != null; }).map(function (row) {
        return (row.ram_gb != null ? row.ram_gb + 'GB' : 'RAM not stated') + ' / ' +
          (row.storage_gb != null ? row.storage_gb + 'GB' : 'storage not stated');
      });
      return '<th scope="col">' + escapeHtml(displayPhoneName(selected.card)) +
        '<br><small>' + escapeHtml(Array.from(new Set(variants)).join('; ') || 'Memory not confirmed') +
        '</small><br><small>' + totals[index] + '/' + fields.length + ' documented comparison fields</small></th>';
    }).join('');
    var rows = fields.map(function (field) {
      return '<tr><th scope="row">' + escapeHtml(field[0]) + '</th>' +
        comparisonSelection.map(function (selected) { return '<td>' + evidence(selected.card, field[1]).html + '</td>'; }).join('') +
        '</tr>';
    }).join('');
    comparePanel.innerHTML = '<div class="research-comparison-heading"><h3>Compare your shortlist (' +
      comparisonSelection.length + '/3)</h3><button type="button" class="btn btn-ghost" data-research-compare-clear>Clear comparison</button></div>' +
      '<p>Saved on this device when browser storage is available. Remove phones or clear anytime; no login needed.</p>' +
      '<p>Side-by-side documented specifications with per-field evidence links. Missing data is not a disadvantage or a zero score. There is no performance winner asserted from specification differences alone.</p>' +
      '<div class="research-table-scroll" role="region" aria-label="Phone specification comparison" tabindex="0">' +
      '<table class="research-spec-table"><caption>Documented specifications and evidence for selected models</caption><thead><tr><th scope="col">Specification</th>' +
      header + '</tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p>Verify exact RAM/storage, regional variant, and current retailer listing before buying. Manufacturer claims are not hands-on test results.</p>';
  }

  function sortResearchMatches(matches, query) {
    var text = normalizeResearch(query);
    var priorityKeys = researchFeatureKeys(query);
    function verifiedSpecCount(card, keys) {
      var specs = card.specifications || {};
      return keys.filter(function (key) {
        var item = specs[key];
        return !!(item && item.value != null && String(item.value).trim() !== "" &&
          /^https:\/\/[^\\s<>"']+$/i.test(String(item.source_url || "")));
      }).length;
    }
    function relevantEvidenceCount(card) {
      return verifiedSpecCount(card, priorityKeys);
    }
    return matches.slice().sort(function (a, b) {
      var aExact = normalizeResearch(a.card.brand + " " + a.card.model) === text ? 1 : 0;
      var bExact = normalizeResearch(b.card.brand + " " + b.card.model) === text ? 1 : 0;
      if (aExact !== bExact) return bExact - aExact;
      // Prioritize documented evidence for the requested topic; never infer a performance winner.
      var aRelevant = relevantEvidenceCount(a.card), bRelevant = relevantEvidenceCount(b.card);
      if (aRelevant !== bRelevant) return bRelevant - aRelevant;
      var aEvidence = verifiedSpecCount(a.card, Object.keys(a.card.specifications || {}));
      var bEvidence = verifiedSpecCount(b.card, Object.keys(b.card.specifications || {}));
      return bEvidence - aEvidence || String(a.card.model).localeCompare(String(b.card.model));
    });
  }



  function showAppliedConditions(query) {
    var c = researchConstraints(query), labels = [];
    if (query) {
      [["Camera", /camera|कैमरा/], ["Battery", /battery|बैटरी/], ["Gaming", /gaming|game|गेमिंग/], ["Display", /display|screen|डिस्प्ले/], ["Software support", /software|support|update|android/], ["Build / reliability", /build|reliability|durability/]].forEach(function (item) { if (item[1].test(c.text)) labels.push("Priority: " + item[0]); });
      if (c.budget != null) labels.push("Reference range: ₹" + Number(c.lower).toLocaleString("en-IN") + " to " + (c.inclusive ? "₹" : "below ₹") + Number(c.budget).toLocaleString("en-IN"));
      if (c.ram != null) labels.push("Exact physical RAM: " + c.ram + "GB");
      if (c.storage != null) labels.push("Exact storage: " + c.storage + "GB");
      var excluded = excludedBrand(c.text); if (excluded) labels.push("Exclude: " + excluded);
      if (c.need5g) labels.push("5G required");
      if (c.needOis) labels.push("OIS required");
      if (c.minimumBattery != null) labels.push("Battery capacity ≥ " + c.minimumBattery + "mAh");
      if (c.minimumRefresh != null) labels.push("Refresh rate ≥ " + c.minimumRefresh + "Hz");
    }
    if (appliedFilters) { appliedFilters.hidden = labels.length === 0; appliedFilters.innerHTML = labels.map(function (label) { return '<span class="research-condition">' + escapeHtml(label) + '</span>'; }).join(''); }
    if (clearSearchButton) clearSearchButton.hidden = !query;
  }

  function researchGuideFallback() {
    return '<p class="standard-guide-fallback"><a class="btn btn-ghost" href="/guides/smartphone-buying-guide/">Standard Buying Guide</a></p>';
  }

  function unpricedResearchLeads(query) {
    var c = researchConstraints(query);
    if (c.budget == null || (c.lower != null && c.lower > c.budget)) {
      return {count: 0, html: ""};
    }
    // Same model, brand, RAM/storage, 5G, OIS and feature constraints as
    // the budget-qualified search. ONLY the dated price-reference gate
    // is relaxed. These are NOT within-budget recommendations.
    var leads = findResearchMatches(query, true).filter(function (item) {
      var ref = item.card.research_budget_reference;
      // A model with a dated numeric reference belongs in budget checking,
      // not in the explicitly price-unknown lane (even when above the cap).
      if (ref && Number(ref.reference_price_inr) > 0) return false;
      var sourced = Object.values(item.card.specifications || {}).filter(function (field) {
        return field && field.value != null && String(field.value).trim() &&
          /^https:\/\//.test(String(field.source_url || ""));
      });
      return sourced.length >= 2;
    }).slice(0, 4);
    var identityOnly = /\b(?:samsung|oneplus|apple|iphone|pixel|redmi|xiaomi|poco|realme|vivo|oppo|motorola|nothing|iqoo|lava|tecno|infinix|honor|nokia|hmd)\b/i.test(String(query || "")) && !/\bexact\s+model\b/i.test(String(query || ""));
    var html = '<section class="research-budget-tier research-budget-unpriced' + (identityOnly ? ' research-identity-only' : '') + '" aria-label="Related phones with unverified price">' +
      '<h3>Additional relevant phones · price not verified (' + leads.length + ')</h3>' +
      '<p>' + (identityOnly ? 'Verification pending: ' : '') + 'These phones match your other documented conditions, but we cannot confirm that their exact RAM/storage variant falls within your selected budget. They may cost more and are not budget-qualified. They are not ranked, in-stock or purchasable recommendations.</p>';
    if (!leads.length) {
      html += '<p>No additional manufacturer/source-linked research matched all the other requested conditions.</p>';
    } else {
      html += '<div class="research-budget-related-list">' + leads.map(function (item) {
        var card = item.card;
        var proof = Object.values(card.specifications || {}).find(function (field) {
          return field && field.value != null && /^https:\/\//.test(String(field.source_url || ""));
        });
        return '<article class="research-budget-related-item">' +
          '<strong>' + escapeHtml(displayPhoneName(card)) + '</strong>' +
          '<span class="research-budget-unknown-label">Price not verified</span>' +
          '<p>' + escapeHtml(card.status === "RESEARCH_ONLY" ? "Model research only" : "Source-backed specifications") +
          ' · ' + escapeHtml(card.research_checked_at || "check date unavailable") +
          ' · ' + (proof ? link(proof.source_url, 'Technical source') : 'Technical source unavailable') + '</p>' +
          '<button type="button" class="btn btn-ghost" data-research-detail="' +
          escapeHtml(card.model_key) + '">View specifications &amp; retailer searches</button></article>';
      }).join("") + '</div>';
    }
    return {count: leads.length, html: html + '</section>'};
  }

  function repositoryFallbackMatches(query) {
    var c = researchConstraints(query), text = c.text;
    var excluded = excludedBrand(text);
    var featureKeys = researchFeatureKeys(text);
    if (/\bnearby\s+(?:band|budget)\b/i.test(String(query || ''))) return [];
    if (c.lower != null && c.budget != null && c.lower > c.budget) return [];
    var brandHints = ['samsung', 'oneplus', 'apple', 'iphone', 'pixel', 'redmi', 'xiaomi', 'poco', 'realme', 'vivo', 'oppo', 'motorola', 'nothing', 'iqoo', 'lava', 'tecno', 'infinix', 'honor', 'nokia', 'hmd'];
    var hintedBrand = excluded ? null : brandHints.find(function (brand) { return new RegExp('\\b' + brand + '\\b', 'i').test(text); });
    if (!/\bexact\s+model\b/i.test(String(query || '')) && /\b(?:iphone|galaxy|pixel)\s+\d/i.test(text)) return [];
    var identityNoise = new Set(['best', 'good', 'better', 'phone', 'phones', 'mobile', 'mobiles', 'smartphone', 'smartphones', 'camera', 'battery', 'gaming', 'game', 'display', 'screen', 'software', 'support', 'update', 'updates', 'student', 'study', 'college', 'school', 'priority', 'recommend', 'recommendation', 'show', 'find', 'need', 'looking', 'for', 'under', 'below', 'within', 'budget', 'price', 'exact', 'model', 'models', 'only', 'preferred', 'want', 'with', 'without', 'nahi', 'nahin', 'chahiye', 'compromise', 'ke', 'liye', 'par', 'pe', 'tak', 'andar', 'se', 'kam', 'mein', 'me', 'का', 'की', 'के', 'में', 'मुझे', 'चाहिए', 'कैमरा', 'बैटरी', 'गेमिंग', 'नहीं']);
    var identityTokens = text.split(' ').filter(function (token) { return token && token.length >= 3 && !identityNoise.has(token) && !/^\d+(?:k|gb|tb)?$/.test(token) && !brandHints.includes(token); });
      var broadTopicQuery = /(?:camera|battery|gaming|game|student|study|college|school|software|support|update|display|screen|build|reliability|durability|कैमरा|बैटरी|गेमिंग|स्टूडेंट|पढ़ाई)/i.test(String(query || ''));
      var topicHasUnknownIdentity = identityTokens.some(function (token) {
        return !inventoryCards.some(function (card) { return normalizeResearch(displayPhoneName(card)).split(' ').indexOf(token) >= 0; });
      });
      if (broadTopicQuery && !topicHasUnknownIdentity) identityTokens = [];
    var explicitModelIdentity = identityTokens.length >= 2 && inventoryCards.some(function (card) {
      var nameTokens = normalizeResearch(displayPhoneName(card)).split(' ');
      return identityTokens.every(function (token) { return nameTokens.indexOf(token) >= 0; });
    });
    var unknownModelIdentity = identityTokens.some(function (token) {
      return !inventoryCards.some(function (card) { return normalizeResearch(displayPhoneName(card)).split(' ').indexOf(token) >= 0; });
    });
    // Keep known exact-model requests tied to that catalogue identity; do not
    // broaden unsupported variants or unknown models into generic results.
    var exactKnownIdentity = explicitModelIdentity && /\bexact\s+model\b/i.test(String(query || '')) && !unknownModelIdentity;
    if ((explicitModelIdentity || unknownModelIdentity) && !exactKnownIdentity) return [];
    var candidates = inventoryCards.map(function (card) {
      return { card: card, rows: inventoryRowsForCard(card) };
    }).filter(function (item) {
      if (excluded && normalizeResearch(item.card.brand).indexOf(excluded) >= 0) return false;
      if (hintedBrand && normalizeResearch(item.card.brand + ' ' + item.card.model).indexOf(hintedBrand) < 0) return false;
      if (exactKnownIdentity) {
        var cardName = normalizeResearch(displayPhoneName(item.card)).split(' ');
        if (!identityTokens.every(function (token) { return cardName.indexOf(token) >= 0; })) return false;
      }
      return true;
    });
    // If a requested brand has no approved catalogue record, still answer with
    // related repository mobiles rather than inventing or silently failing.
    if (!candidates.length && hintedBrand && !exactKnownIdentity) {
      candidates = inventoryCards.map(function (card) {
        return { card: card, rows: inventoryRowsForCard(card) };
      }).filter(function (item) {
        return !(excluded && normalizeResearch(item.card.brand).indexOf(excluded) >= 0);
      });
    }
    // Prefer records with source-backed fields relevant to the request, while
    // keeping the fallback explicitly separate from exact constraint matching.
    candidates.sort(function (a, b) {
      function score(item) {
        var specs = item.card.specifications || {};
        var relevant = featureKeys.filter(function (key) {
          var field = specs[key];
          return field && field.value != null && /^https:\/\//i.test(String(field.source_url || ''));
        }).length;
        var evidence = Object.keys(specs).filter(function (key) {
          var field = specs[key];
          return field && field.value != null && /^https:\/\//i.test(String(field.source_url || ''));
        }).length;
        return relevant * 100 + evidence;
      }
      return score(b) - score(a) || String(a.card.model).localeCompare(String(b.card.model));
    });
    return candidates.slice(0, 3);
  }

  function relatedRepositoryResearch(query, items) {
    if (!items.length) return '';
    return '<section class="research-context research-related-repository">' +
      '<h3>Related repository mobiles — exact request not confirmed</h3>' +
      '<p>These are approved mobile records from our research catalogue. They are shown for further research only; they do not satisfy every budget, memory, brand or feature condition in the query.</p>' +
      items.map(function (item) { return renderResearchResultCard(item.card, item.rows, 1); }).join('') +
      '</section>';
  }

  function emptyResearchResult(query, fallback) {
    var c = researchConstraints(query);
    var message = "No documented match in our saved research for this request.";
    if (c.lower != null && c.budget != null && c.lower > c.budget) message = "The lower budget is higher than the upper budget. Please correct the range.";
    else if (c.ram != null || c.storage != null) message += " We cannot confirm the requested exact memory variant with all these conditions.";
    else if (c.budget != null) message += " No matching record passes this price band and the other conditions. Missing references and recorded out-of-stock entries are excluded.";
    return '<div class="mobile-research-empty"><p>' + escapeHtml(message) + '</p><p>This is a research coverage gap, not proof that no suitable phone exists. No constraint has been relaxed for budget-qualified results.</p><a href="#mobileResearchCatalogue">Browse the full research catalogue</a>' + researchGuideFallback() + '</div>' + relatedRepositoryResearch(query, fallback || []);
  }

  function verifiedRecommendationBridge(query, isComparison, matches) {
    var c = researchConstraints(query);
    if (isComparison || c.budget == null) return "";
    var topThree = /\btop\s*3\b/i.test(String(query || "")) ? (matches || []).slice(0, 3) : [];
    var topThreeHtml = topThree.length ? '<section class="research-verified-top3" aria-label="Research-Verified top 3"><h3>Research-Verified top 3 for this budget band</h3><p>Ordered by source coverage and constraint fit, not a measured performance winner. Current price and current stock are not verified.</p><div class="research-top3-grid">' +
      topThree.map(function (item) { return '<div class="research-top3-result">' + renderResearchResultCard(item.card, item.rows, item.group_size) + '</div>'; }).join("") + '</div></section>' : "";
    return topThreeHtml + '<div class="research-context research-verified-recommendations">' +
      '<p><strong>Need a performance-based recommendation?</strong> This list is ordered by research coverage, not proven camera, gaming or battery performance. Check the existing recommendation engine separately; it will show results only when its evidence and eligibility rules pass.</p>' +
      '<button type="button" class="btn btn-ghost" data-research-verified-recommend>Check eligible recommendations</button></div>';
  }

  function searchResearch(query) {
    var nextQuery = String(query || "").trim();
    var queryChanged = nextQuery !== lastSearchQuery;
    if (queryChanged) {
      searchExpanded = false;
      if (typeof window.CouponWorldCancelShoppingRecommendation === "function") {
        window.CouponWorldCancelShoppingRecommendation();
      }
    }
    lastSearchQuery = nextQuery;
    showAppliedConditions(lastSearchQuery);
    if (researchQuery && researchQuery.value !== nextQuery) researchQuery.value = nextQuery;
    if (!lastSearchQuery) {
      if (researchResults) { researchResults.hidden = true; researchResults.innerHTML = ""; }
      if (researchResultsMore) researchResultsMore.hidden = true;
      if (researchSearchStatus) researchSearchStatus.textContent = "";
      lastStrictMatchCount = 0;
      return [];
    }
    revealSearch();
    if (!inventoryCards.length) { if (researchSearchStatus) researchSearchStatus.textContent = inventoryLoadFailed ? "Saved smartphone research is temporarily unavailable." : "Loading smartphone research…"; if (researchResults) { researchResults.hidden = false; researchResults.innerHTML = researchGuideFallback(); } return []; }
    var parts = lastSearchQuery.replace(/^compare\s+/i, "").split(/\s+(?:vs\.?|versus|और|compare)\s+/i);
    if (/^compare\s/i.test(lastSearchQuery) && parts.length === 1) parts = parts[0].split(/\s+and\s+/i);
    var comparison = parts.length > 1;
    var missingComparison = false;
    var matches;
    if (comparison) {
      matches = [];
      parts.slice(0, 4).forEach(function (part) {
        var group = findResearchMatches(part);
        if (!group.length) missingComparison = true;
        group.slice(0, 1).forEach(function (item) { if (!matches.some(function (existing) { return existing.card.model_key === item.card.model_key; })) matches.push(item); });
      });
    } else {
      matches = findResearchMatches(lastSearchQuery);
    }
    var c = researchConstraints(lastSearchQuery);
    var validBudget = !comparison && c.budget != null && (c.lower == null || c.lower <= c.budget);
    matches = groupResearchMatches(matches);
    lastStrictMatchCount = matches.length;
    // Never broaden an explicit budget band into unrelated catalogue matches.
    // The price-unknown lane below is the only allowed additional context.
    var fallback = matches.length || validBudget ? [] : repositoryFallbackMatches(lastSearchQuery);
    var displayMatches = matches.length ? matches : fallback;
    lastSearchMatches = displayMatches;
    var visible = searchExpanded ? displayMatches : displayMatches.slice(0, MAX_SEARCH_RESULTS);
    if (comparison && queryChanged) {
      comparisonSelection = matches.slice(0, 3);
      persistShortlist();
      renderSelectedComparison();
    }
    var additional = validBudget ? unpricedResearchLeads(lastSearchQuery) : {count: 0, html: ""};
    if (researchResults) {
      researchResults.hidden = false;
      var bridge = verifiedRecommendationBridge(lastSearchQuery, comparison, matches);
      if (validBudget) {
        // Local, synchronous two-lane answer. No network round trip or
        // third-party API is required before either lane appears.
        var primary = '<section class="research-budget-tier research-budget-evidenced" aria-label="Phones with dated budget references">' +
          '<h3>Within your budget · dated price reference (' + matches.length + ')</h3>' +
          '<p>These source-backed variants pass the selected historical reference-price limit. Current checkout price, availability and delivery have NOT been confirmed. Ordering shows research coverage, not measured performance.</p>' +
          (matches.length ?
            '<div class="research-budget-primary-grid">' + visible.map(function (item) {
              return renderResearchResultCard(item.card, item.rows, item.group_size);
            }).join("") + '</div>' :
            '<p>No saved dated price reference passes every condition. This does not prove that no suitable phone exists.</p>') +
          '</section>';
        researchResults.innerHTML = bridge + primary + additional.html +
          (!matches.length && !additional.count ? relatedRepositoryResearch(lastSearchQuery, visible) : '');
      } else {
        researchResults.innerHTML = bridge +
          (comparison ? '<p class="mobile-research-gate">Specification comparison; no performance winner is asserted.' +
            (missingComparison ? ' At least one requested model or memory variant could not be matched.' : '') + '</p>' : '') +
          (matches.length ? visible.map(function (item) {
            return renderResearchResultCard(item.card, item.rows, item.group_size);
          }).join("") : emptyResearchResult(lastSearchQuery, visible));
      }
    }
    if (researchSearchStatus) {
      if (validBudget) {
        researchSearchStatus.textContent = matches.length + " dated budget-reference matches · " +
          additional.count + " related phones with price unverified · local research results";
        researchSearchStatus.textContent += " · requested range ₹" +
          Number(c.lower).toLocaleString("en-IN") + " to " +
          (c.inclusive ? "₹" : "below ₹") + Number(c.budget).toLocaleString("en-IN");
      } else {
        researchSearchStatus.textContent = matches.length ? matches.length + " matching research model" +
          (matches.length === 1 ? "" : "s") + " · showing " + visible.length :
          "No exact catalogue match · showing " + visible.length + " related repository research model" +
          (visible.length === 1 ? "" : "s") + " for further research";
      }
      if (/best|अच्छा|अच्छे/i.test(lastSearchQuery)) researchSearchStatus.textContent +=
        " · evidence coverage order, not a performance ranking";
      if (researchResults && String(researchResults.innerHTML || "").indexOf("research-verified-top3") >= 0) researchSearchStatus.textContent += " · research picks";
    }
    if (researchResultsMore) { researchResultsMore.hidden = displayMatches.length <= MAX_SEARCH_RESULTS; researchResultsMore.textContent = searchExpanded ? "Show fewer results" : "Load more research results"; }
    return displayMatches;
  }

  function submitResearch(query) {
    var submitted = String(query || "").trim();
    if (submitted) trackResearchEvent("research_search_submit", {
      search_intent: researchIntent(submitted),
      comparison_query: /\b(?:compare|vs\.?|versus)\b|और/i.test(submitted) ? 1 : 0
    });
    // Reuse the just-computed strict match count. Do not repeat the full
    // catalogue scan (and never block local answers on retailer/API latency).
    searchResearch(query);
    if (inventoryCards.length && lastStrictMatchCount > 0 &&
        researchConstraints(query).budget != null &&
        !/\b(?:compare|vs\.?|versus)\b|और/i.test(String(query || "")) &&
        typeof window.CouponWorldShoppingRecommend === "function") {
      window.CouponWorldShoppingRecommend(query, {background: true});
    }
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
    detailSection.dataset.modelKey = modelKey;
    if (detailTitle) detailTitle.textContent = displayPhoneName(card);
    detailContent.innerHTML = renderInventoryCard(card) + '<p class="mobile-research-gate">Research detail only · check current price and availability with retailers.</p>';
    var specifications = detailContent.querySelector("details.mobile-research-model-details");
    if (specifications) specifications.open = true;
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
    // Keep this section genuinely recent without requiring a commerce claim.
    // Market-intake research remains visible even when its launch date is not
    // recorded; dated India launch evidence is limited to the last 365 days.
    var recentLaunchCutoff = Date.now() - 365 * 24 * 60 * 60 * 1000;
    var recent = inventoryCards.filter(function (card) {
      if (card.market_intake !== true || !(card.source_urls || []).length) return false;
      if (!card.india_launch_date) return true;
      if (!card.india_launch_date) return true;
      var launchTime = Date.parse(String(card.india_launch_date) + "T00:00:00Z");
      return Number.isFinite(launchTime) && launchTime >= recentLaunchCutoff;
    }).sort(function (a, b) {
      return Number(Boolean(b.recent_source_intake)) - Number(Boolean(a.recent_source_intake)) ||
        String(b.research_checked_at || "").localeCompare(String(a.research_checked_at || "")) ||
        String(a.model_key).localeCompare(String(b.model_key));
    });
    researchNewSection.hidden = recent.length === 0;
    var counter = document.getElementById("mobileResearchNewCount");
    if (counter) counter.textContent = recent.length + " additional India research models, separate from the original 232";
    if (!recent.length) {
      researchNewGrid.innerHTML = "";
      return;
    }
    var first = recent.slice(0, 6).map(function (card) {
      return renderResearchResultCard(card, inventoryRowsForCard(card));
    }).join("");
    var rest = recent.slice(6).map(function (card) {
      return renderResearchResultCard(card, inventoryRowsForCard(card));
    }).join("");
    researchNewGrid.innerHTML = first + (rest ?
      '<details class="recent-mobile-more"><summary>Show all ' + recent.length +
      ' newly added phones (' + (recent.length - 6) + ' more)</summary>' +
      '<div class="mobile-research-results">' + rest + '</div></details>' : '');
  }

  fetch("/data/mobile_research_preview.json", { credentials: "omit" })
    .then(function (response) {
      if (!response.ok) throw new Error("research preview unavailable");
      return response.json();
    })
    .then(function (payload) {
      var products = Array.isArray(payload.products) ? payload.products : [];
      verifiedRows = products;
      verifiedById = new Map(products.map(function (row) { return [row.canonical_product_id, row]; }));
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

  if (guidedApply) guidedApply.addEventListener("click", function () {
    var values = guidedControls.map(function (control) { return String(control && control.value || ""); });
    if (!values.some(Boolean)) { if (guidedStatus) guidedStatus.textContent = "Choose a budget, priority, exact memory or brand exclusion to start."; return; }
    var query = (values[1] ? values[1] + " " : "") + "phone";
    if (values[0]) query += " under " + values[0] + (guidedScope && guidedScope.value === "band" ? " nearby band" : " full budget");
    if (values[2]) query += " " + values[2] + "GB physical RAM";
    if (values[3]) query += " " + values[3] + "GB storage";
    if (values[4]) query += " exclude " + values[4];
    if (guidedStatus) guidedStatus.textContent = "Search built from your selected conditions.";
    var hero = document.getElementById("heroSearch"); if (hero) hero.value = query;
    submitResearch(query);
  });
  if (clearSearchButton) clearSearchButton.addEventListener("click", function () {
    guidedControls.forEach(function (control) { if (control) control.value = ""; });
    if (guidedScope) guidedScope.value = "band";
    if (guidedStatus) guidedStatus.textContent = "";
    var hero = document.getElementById("heroSearch"); if (hero) hero.value = "";
    searchResearch("");
  });
  if (researchSearchButton) researchSearchButton.addEventListener("click", function () { submitResearch(researchQuery && researchQuery.value); });
  if (researchQuery) researchQuery.addEventListener("keydown", function (event) { if (event.key === "Enter") submitResearch(researchQuery.value); });
  document.querySelectorAll("[data-mobile-research-query]").forEach(function (button) {
    button.addEventListener("click", function () { var requested = button.getAttribute("data-mobile-research-query") || "";
      var current = researchQuery && researchQuery.value || "";
      if (current && researchConstraints(current).budget != null && researchConstraints(requested).budget == null) {
        var constraintsOnly = current.replace(/camera|battery|gaming|game|software|support|display|screen|कैमरा|बैटरी|गेमिंग/gi, " ");
        requested = requested + " " + constraintsOnly;
      }
      if (researchQuery) researchQuery.value = requested;
      submitResearch(requested); });
  });
  if (researchResultsMore) researchResultsMore.addEventListener("click", function () {
    searchExpanded = !searchExpanded;
    trackResearchEvent("research_results_expand", { expanded: searchExpanded ? 1 : 0, search_intent: researchIntent(lastSearchQuery) });
    searchResearch(lastSearchQuery);
  });
  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-research-verified-recommend]")) {
      if (typeof window.CouponWorldShoppingRecommend === "function" && lastSearchQuery) {
        window.CouponWorldShoppingRecommend(lastSearchQuery);
      } else if (researchSearchStatus) {
        researchSearchStatus.textContent = "Recommendation service is unavailable. Research results remain accessible.";
      }
      return;
    }
    var compareButton = event.target.closest("[data-research-compare]");
    if (compareButton) {
      var candidate = lastSearchMatches.find(function (item) { return item.card.model_key === compareButton.getAttribute("data-research-compare"); });
      if (!candidate) {
        var sourceCard = inventoryCards.find(function (card) { return card.model_key === compareButton.getAttribute("data-research-compare"); });
        if (sourceCard) candidate = {card: sourceCard, rows: inventoryRowsForCard(sourceCard)};
      }
      if (candidate) {
        var existing = comparisonSelection.findIndex(function (item) { return researchGroupKey(item.card) === researchGroupKey(candidate.card); });
        if (existing >= 0) comparisonSelection.splice(existing, 1);
        else if (comparisonSelection.length < 3) comparisonSelection.push(candidate);
        else { if (researchSearchStatus) researchSearchStatus.textContent = "Compare up to 3 phones. Remove one before adding another."; return; }
        trackResearchEvent("research_compare_toggle", { compare_action: existing >= 0 ? "remove" : "add", selection_count: comparisonSelection.length });
        persistShortlist();
        renderSelectedComparison(); searchResearch(lastSearchQuery);
        if (comparisonSelection.length >= 2 && comparePanel) comparePanel.scrollIntoView({behavior: "smooth", block: "start"});
      }
    }
    if (event.target.closest("[data-research-compare-clear]")) {
      comparisonSelection = [];
      trackResearchEvent("research_compare_clear", { selection_count: 0 });
      persistShortlist();
      renderSelectedComparison(); searchResearch(lastSearchQuery);
    }
    // A photo tap reveals the retailer choices beside the selected photo.
    // Reuse the existing verified-vs-search retailer gate; never invent links.
    var photoButton = event.target.closest(".research-photo-open[data-research-detail]");
    if (photoButton) {
      event.preventDefault();
      var photoModel = photoButton.getAttribute("data-research-detail");
      var photoCard = inventoryCards.find(function (item) { return item.model_key === photoModel; });
      if (photoCard) {
        var photoHost = photoButton.closest(".research-phone-photo, .mobile-research-inventory-card, .mobile-research-result-card") || photoButton.parentElement;
        var existingChoices = photoHost.querySelector(".research-photo-retailer-panel");
        if (existingChoices) {
          existingChoices.remove();
          photoButton.setAttribute("aria-expanded", "false");
        } else {
          document.querySelectorAll(".research-photo-retailer-panel").forEach(function (panel) {
            panel.remove();
          });
          document.querySelectorAll(".research-photo-open[aria-expanded='true']").forEach(function (button) {
            button.setAttribute("aria-expanded", "false");
          });
          var choices = document.createElement("div");
          choices.className = "research-photo-retailer-panel";
          choices.setAttribute("role", "region");
          choices.setAttribute("aria-label", "Retailer choices for " + displayPhoneName(photoCard));
          choices.innerHTML = '<strong>' + escapeHtml(displayPhoneName(photoCard)) + '</strong>' +
            '<p>Choose a retailer · verify variant, price and availability there.</p>' +
            retailerResearchLinks(photoCard) +
            '<button type="button" class="btn btn-ghost" data-research-detail="' +
            escapeHtml(photoModel) + '">View full specifications</button>';
          photoButton.insertAdjacentElement("afterend", choices);
          photoButton.setAttribute("aria-expanded", "true");
        }
      }
      return;
    }
    var detail = event.target.closest("[data-research-detail]");
    if (detail) {
      event.preventDefault();
      var selectedModel = detail.getAttribute("data-research-detail");
      if (detailSection && !detailSection.hidden && detailSection.dataset.modelKey === selectedModel) {
        detailSection.hidden = true;
        delete detailSection.dataset.modelKey;
        window.location.hash = "mobileResearchPreview";
      } else {
        window.location.hash = "mobileResearchDetail/" + encodeURIComponent(selectedModel);
        showDetail(selectedModel);
      }
    }
    var linkTarget = event.target.closest('a[href="#mobileResearchPreview"], a[href="#mobileResearchCatalogue"]');
    if (linkTarget) {
      if (linkTarget.getAttribute("href") === "#mobileResearchPreview") revealPreview();
      if (linkTarget.getAttribute("href") === "#mobileResearchCatalogue") revealCatalogue();
    }
  });
  if (savedShortlistButton) savedShortlistButton.addEventListener("click", function () {
    if (comparePanel && !comparePanel.hidden) {
      comparePanel.scrollIntoView({behavior: "smooth", block: "start"});
      comparePanel.focus({preventScroll: true});
    }
  });
  window.addEventListener("hashchange", handleResearchHash);
  window.CouponWorldMobileResearch = {
    isResearchQuery: function (value) {
      return researchConstraints(value).budget != null || /(?:phone|mobile|smartphone|galaxy|samsung|iphone|pixel|redmi|oneplus|nothing|realme|vivo|oppo|xiaomi|motorola|poco|iqoo|lava|tecno|infinix|camera|battery|gaming|display|software|build|reliability|durability|android|ram|storage|फोन|मोबाइल|कैमरा|बैटरी|गेमिंग|सैमसंग|अच्छा)/i.test(String(value || ""));
    },
    search: searchResearch,
    submit: submitResearch,
    clear: function () { if (researchQuery) researchQuery.value = ""; searchResearch(""); },
    revealPreview: revealPreview,
    revealCatalogue: revealCatalogue
  };
  loadInventoryCatalogue();
}());

