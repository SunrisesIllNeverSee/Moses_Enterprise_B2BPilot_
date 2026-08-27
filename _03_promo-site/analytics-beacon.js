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
  };
})();
