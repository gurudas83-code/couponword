/* Use the site's existing GA4 property. Send platform categories, not raw queries. */
(function () {
  'use strict';
  function platform(value) {
    var host;
    try { host = new URL(value).hostname.toLowerCase(); } catch (_) { return 'direct_or_unattributed'; }
    var groups = [
      ['chatgpt', ['chatgpt.com', 'chat.openai.com']],
      ['gemini', ['gemini.google.com']],
      ['meta_ai', ['meta.ai']],
      ['perplexity', ['perplexity.ai']],
      ['copilot', ['copilot.microsoft.com']],
      ['claude', ['claude.ai']],
      ['google', ['google.com', 'google.co.in']],
      ['bing', ['bing.com']],
      ['meta_social', ['facebook.com', 'instagram.com', 'threads.net']]
    ];
    for (var i = 0; i < groups.length; i++) {
      if (groups[i][1].some(function (domain) { return host === domain || host.endsWith('.' + domain); })) return groups[i][0];
    }
    return 'other_referral';
  }
  function arrival() {
    var ref = platform(document.referrer);
    var source = new URLSearchParams(window.location.search).get('utm_source');
    var known = {chatgpt:'chatgpt', 'chatgpt.com':'chatgpt', gemini:'gemini', 'gemini.google.com':'gemini', meta:'meta_ai', 'meta.ai':'meta_ai', perplexity:'perplexity', 'perplexity.ai':'perplexity', copilot:'copilot', claude:'claude', google:'google', bing:'bing'};
    var result = source && known[source.toLowerCase()] || ref;
    try {
      var internal = document.referrer && new URL(document.referrer).origin === window.location.origin;
      var previous = JSON.parse(window.sessionStorage.getItem('cw_discovery_source') || 'null');
      if (internal && !source && previous && Date.now() - previous.at < 30 * 60 * 1000) result = previous.source;
      window.sessionStorage.setItem('cw_discovery_source', JSON.stringify({source:result,at:Date.now()}));
    } catch (_) { /* Browsing and analytics still work if storage is unavailable. */ }
    return result;
  }
  function send(name, params) {
    if (typeof window.gtag === 'function') window.gtag('event', name, params);
  }
  // Field-speed evidence: browser-collected signals, not synthetic CI claims.
  // Only aggregate durations; never collect addresses, queries or user IDs.
  function observeVitals(discoverySource) {
    if (!window.PerformanceObserver || !window.performance) return;
    var measurements = {lcp_ms: null, cls_milli: 0, inp_ms: null};
    var cls = 0, maxInteraction = 0;
    function watch(type, onEntry) {
      try {
        var observer = new window.PerformanceObserver(function (list) {
          list.getEntries().forEach(onEntry);
        });
        observer.observe({type: type, buffered: true});
      } catch (_) { /* Unsupported web-vital signal: do not fabricate a value. */ }
    }
    watch('largest-contentful-paint', function (entry) {
      var measured = entry.renderTime || entry.loadTime || entry.startTime;
      if (Number.isFinite(measured) && measured >= 0) measurements.lcp_ms = Math.round(measured);
    });
    watch('layout-shift', function (entry) {
      if (!entry.hadRecentInput && Number.isFinite(entry.value)) cls += entry.value;
    });
    watch('event', function (entry) {
      if (entry.interactionId && Number.isFinite(entry.duration)) {
        maxInteraction = Math.max(maxInteraction, entry.duration);
      }
    });
    var sent = false;
    function report() {
      if (sent) return;
      sent = true;
      var navigation = window.performance.getEntriesByType && window.performance.getEntriesByType('navigation')[0];
      var event = {
        discovery_source: discoverySource,
        page_kind: window.location.pathname.indexOf('/phones/') === 0 ? 'phone' : 'other',
        device_width_bucket: window.innerWidth < 600 ? 'small' : window.innerWidth < 1024 ? 'medium' : 'large'
      };
      if (measurements.lcp_ms !== null) event.lcp_ms = measurements.lcp_ms;
      if (cls >= 0) event.cls_milli = Math.round(cls * 1000);
      if (maxInteraction > 0) event.inp_proxy_ms = Math.round(maxInteraction);
      if (navigation && Number.isFinite(navigation.responseEnd)) event.response_end_ms = Math.round(navigation.responseEnd);
      if (Object.keys(event).length > 3) send('cw_field_performance', event);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') report();
    });
    window.addEventListener('pagehide', report);
  }
  var source = arrival();
  observeVitals(source);
  var path = window.location.pathname;
  send('discovery_landing', {discovery_source:source, landing_path:path, page_kind:path.indexOf('/phones/') === 0 ? 'phone_specification' : path.indexOf('/seo/') === 0 ? 'phone_guide' : path.indexOf('/guides/') === 0 ? 'guide_collection' : 'research'});
  document.addEventListener('click', function (event) {
    var anchor = event.target.closest && event.target.closest('a[href]');
    if (!anchor) return;
    var target;
    try { target = new URL(anchor.href, window.location.href); } catch (_) { return; }
    var kind = '';
    if (target.origin === window.location.origin) {
      if (target.pathname.indexOf('/phones/') === 0) kind = 'open_phone_specification';
      else if (target.pathname.indexOf('/seo/') === 0) kind = 'open_guide';
      else if (target.pathname.indexOf('/compare/') === 0) kind = 'open_compare';
      else if (target.pathname.indexOf('/guides/') === 0) kind = 'open_buying_guide';
      else if (target.pathname.indexOf('/accessories/') === 0 || target.pathname.indexOf('/tvs/') === 0) kind = 'open_category';
      else if (target.pathname === '/' && target.hash === '#mobileResearchSearch') kind = 'start_research';
    } else if (['amazon.in','www.amazon.in','flipkart.com','www.flipkart.com','croma.com','www.croma.com'].includes(target.hostname)) kind = 'retailer_research';
    if (kind) send('discovery_action', {discovery_source:source, action_kind:kind, landing_path:path, destination_host:target.hostname, destination_path:target.pathname});
    // A retailer visit is a measurable outbound lead, NOT an order, purchase or commission.
    if (kind === 'retailer_research') send('cw_retailer_outbound', {
      retailer: target.hostname.replace(/^www\./, ''),
      discovery_source: source,
      page_path: path,
      // Avoid recording affiliate tags, product URLs or private search terms.
      listing_type: /\/search\b|\/s\b/.test(target.pathname) ? 'retailer_search' : 'retailer_page'
    });

    var control = event.target.closest && event.target.closest('[data-mobile-query],[data-mobile-research-query],[data-research-compare],[data-analytics-intent],#heroSearchButton,#mobileResearchSearchButton,#researchGuidedApply,#mobileResearchResultsMore');
    if (control && (typeof control.matches === 'function' || typeof control.getAttribute === 'function')) {
      var action = 'content_cta_click';
      var matches = function (selector) { return typeof control.matches === 'function' && control.matches(selector); };
      if (matches('#heroSearchButton, #mobileResearchSearchButton')) action = 'research_search_submit';
      else if (matches('#researchGuidedApply')) action = 'guided_search_submit';
      else if (matches('[data-research-compare]')) action = 'compare_toggle';
      else if (matches('[data-mobile-query]')) action = 'budget_shortcut';
      else if (matches('[data-mobile-research-query]')) action = 'research_shortcut';
      else if (matches('#mobileResearchResultsMore')) action = 'research_results_expand';
      send('research_action', {
        discovery_source: source,
        action_kind: action,
        intent: typeof control.getAttribute === 'function' ? control.getAttribute('data-analytics-intent') || 'unspecified' : 'unspecified',
        page_path: path
      });
    }
  });
})();
