// MO§ES™ analytics beacon — lightweight, privacy-preserving
// Auto-detects AI crawlers, tracks page views, sends to /api/analytics/beacon
(function() {
  var ua = navigator.userAgent;
  var path = location.pathname;
  var host = location.hostname;

  // Detect if this is an AI crawler (they don't run JS, but just in case)
  var aiBots = ['gptbot','oai-searchbot','chatgpt-user','perplexitybot','claudebot','anthropic-ai','google-extended','bingbot','ccbot','bytespider','applebot'];
  var isAiBot = aiBots.some(function(b) { return ua.toLowerCase().includes(b); });

  // Only beacon for human visitors (bots are tracked server-side via the worker)
  if (isAiBot) return;

  // Page view beacon
  function beacon(type, data) {
    var payload = Object.assign({ type: type, path: path }, data || {});
    try {
      fetch('/api/analytics/beacon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(function() {});
    } catch(e) {}
  }

  // Send pageview
  beacon('pageview', {
    referrer: document.referrer || null,
  });

  // Track AI overview citations (check if visitor came from an AI engine)
  var aiReferrers = {
    'chatgpt.com': 'OpenAI/ChatGPT',
    'perplexity.ai': 'Perplexity',
    'claude.ai': 'Anthropic/Claude',
    'gemini.google.com': 'Google/Gemini',
    'copilot.microsoft.com': 'Microsoft/Copilot',
    'you.com': 'You.com',
    'phind.com': 'Phind',
    'kagi.com': 'Kagi',
  };
  for (var domain in aiReferrers) {
    if (document.referrer && document.referrer.includes(domain)) {
      beacon('ai_overview', {
        aiEngine: aiReferrers[domain],
        aiCited: true,
        referrer: document.referrer,
      });
      break;
    }
  }

  // ─── Core Web Vitals collection ──────────────────────────────────────
  // Collects LCP, INP, CLS, TTFB using native Performance Observer APIs
  // Sends to our analytics worker as 'web_vitals' events
  var vitals = { lcp: null, inp: null, cls: 0, ttfb: null, fid: null };
  var vitalsSent = false;

  function sendVitals() {
    if (vitalsSent) return;
    vitalsSent = true;
    var navTiming = performance.getEntriesByType('navigation')[0];
    if (navTiming) {
      vitals.ttfb = Math.round(navTiming.responseStart - navTiming.requestStart);
      vitals.dns = Math.round(navTiming.domainLookupEnd - navTiming.domainLookupStart);
      vitals.tcp = Math.round(navTiming.connectEnd - navTiming.connectStart);
      vitals.download = Math.round(navTiming.responseEnd - navTiming.responseStart);
    }
    beacon('web_vitals', vitals);
  }

  // LCP — Largest Contentful Paint
  try {
    new PerformanceObserver(function(l) {
      var entries = l.getEntries();
      if (entries.length > 0) {
        vitals.lcp = Math.round(entries[entries.length - 1].startTime);
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch(e) {}

  // CLS — Cumulative Layout Shift
  try {
    new PerformanceObserver(function(l) {
      l.getEntries().forEach(function(e) {
        if (!e.hadRecentInput) vitals.cls += e.value;
      });
    }).observe({ type: 'layout-shift', buffered: true });
  } catch(e) {}

  // INP — Interaction to Next Paint (via event timing)
  try {
    var maxDuration = 0;
    new PerformanceObserver(function(l) {
      l.getEntries().forEach(function(e) {
        if (e.duration > maxDuration) maxDuration = e.duration;
      });
      vitals.inp = Math.round(maxDuration);
    }).observe({ type: 'event', buffered: true });
  } catch(e) {}

  // FID — First Input Delay (legacy, for older browsers)
  try {
    new PerformanceObserver(function(l) {
      var entries = l.getEntries();
      if (entries.length > 0) {
        vitals.fid = Math.round(entries[0].processingStart - entries[0].startTime);
      }
    }).observe({ type: 'first-input', buffered: true });
  } catch(e) {}

  // Send vitals on page hide (best effort, uses sendBeacon fallback)
  window.addEventListener('pagehide', function() {
    // Use sendBeacon for reliability on page unload
    try {
      var payload = JSON.stringify(Object.assign({ type: 'web_vitals', path: path }, vitals));
      navigator.sendBeacon('/api/analytics/beacon', new Blob([payload], { type: 'application/json' }));
    } catch(e) {
      sendVitals();
    }
  });

  // Also send after 10 seconds (in case user stays on page)
  setTimeout(sendVitals, 10000);

  // Expose for manual tracking
  window.mosesAnalytics = {
    beacon: beacon,
    trackAiOverview: function(engine, query, position, cited) {
      beacon('ai_overview', {
        aiEngine: engine, aiQuery: query, aiPosition: position, aiCited: cited,
      });
    },
    trackMcpCall: function(tool) {
      beacon('mcp_call', { tool: tool });
    },
    getVitals: function() { return vitals; },
  };
})();
