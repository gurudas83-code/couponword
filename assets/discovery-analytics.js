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
  var source = arrival();
  var path = window.location.pathname;
  send('discovery_landing', {discovery_source:source, landing_path:path, page_kind:path.indexOf('/seo/') === 0 ? 'phone_guide' : path.indexOf('/guides/') === 0 ? 'guide_collection' : 'research'});
  document.addEventListener('click', function (event) {
    var anchor = event.target.closest && event.target.closest('a[href]');
    if (!anchor) return;
    var target;
    try { target = new URL(anchor.href, window.location.href); } catch (_) { return; }
    var kind = '';
    if (target.origin === window.location.origin) {
      if (target.pathname.indexOf('/seo/') === 0) kind = 'open_guide';
      else if (target.pathname === '/' && target.hash === '#mobileResearchSearch') kind = 'start_research';
    } else if (['amazon.in','www.amazon.in','flipkart.com','www.flipkart.com','croma.com','www.croma.com'].includes(target.hostname)) kind = 'retailer_research';
    if (kind) send('discovery_action', {discovery_source:source, action_kind:kind, landing_path:path, destination_host:target.hostname, destination_path:target.pathname});
  });
})();
