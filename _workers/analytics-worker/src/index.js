// MO§ES™ analytics + crawl control + agent readiness worker
// Serves: analytics beacon, crawl control config, agent readiness manifest,
// analytics query API, bot/AI-crawler tracking via Analytics Engine + KV
//
// Routes (via wrangler.toml):
//   /api/analytics/beacon      — POST: record a page/agent event
//   /api/analytics/stats       — GET:  query aggregated stats
//   /api/analytics/bots        — GET:  bot/AI-crawler visit log
//   /api/analytics/ai-overview — GET:  AI engine visibility tracker
//   /crawl-control.json        — GET:  machine-readable crawl rules
//   /crawl-control             — GET:  human-readable crawl control page
//   /.well-known/agent.json    — GET:  agent readiness manifest
//   /.well-known/ai-crawler-log— POST:  AI crawler self-report endpoint

const AI_CRAWLERS = {
  'gptbot': { engine: 'OpenAI/ChatGPT', type: 'training' },
  'oai-searchbot': { engine: 'OpenAI/Search', type: 'search' },
  'chatgpt-user': { engine: 'OpenAI/ChatGPT', type: 'user' },
  'perplexitybot': { engine: 'Perplexity', type: 'search' },
  'perplexity-ai': { engine: 'Perplexity', type: 'search' },
  'claudebot': { engine: 'Anthropic/Claude', type: 'training' },
  'anthropic-ai': { engine: 'Anthropic/Claude', type: 'training' },
  'claude-user': { engine: 'Anthropic/Claude', type: 'user' },
  'google-extended': { engine: 'Google/Gemini', type: 'training' },
  'googlebot': { engine: 'Google/Search', type: 'search' },
  'bingbot': { engine: 'Microsoft/Copilot', type: 'search' },
  'bingpreview': { engine: 'Microsoft/Copilot', type: 'search' },
  'bytespider': { engine: 'ByteDance/Doubao', type: 'training' },
  'applebot': { engine: 'Apple/Intelligence', type: 'search' },
  'applebot-extended': { engine: 'Apple/Intelligence', type: 'training' },
  'meta-externalagent': { engine: 'Meta/LLaMA', type: 'training' },
  'cohere-ai': { engine: 'Cohere', type: 'training' },
  'amazonbot': { engine: 'Amazon/Rufus', type: 'search' },
  'yandexbot': { engine: 'Yandex', type: 'search' },
  'baiduspider': { engine: 'Baidu', type: 'search' },
  'ccbot': { engine: 'Common Crawl', type: 'training' },
  'facebookbot': { engine: 'Meta', type: 'search' },
  'linkedinbot': { engine: 'LinkedIn', type: 'search' },
  'x-bot': { engine: 'X/Grok', type: 'search' },
  'grok': { engine: 'X/Grok', type: 'search' },
};

// AI referrer domains — when a human visit comes from one of these,
// it counts as a referral from that AI engine (for crawl-to-referral ratio)
const AI_REFERRER_DOMAINS = {
  'chatgpt.com': 'OpenAI/ChatGPT',
  'chat.openai.com': 'OpenAI/ChatGPT',
  'openai.com': 'OpenAI/ChatGPT',
  'perplexity.ai': 'Perplexity',
  'claude.ai': 'Anthropic/Claude',
  'anthropic.com': 'Anthropic/Claude',
  'gemini.google.com': 'Google/Gemini',
  'google.com': 'Google/Search',
  'copilot.microsoft.com': 'Microsoft/Copilot',
  'bing.com': 'Microsoft/Copilot',
  'you.com': 'You.com',
  'poe.com': 'Poe',
  'phind.com': 'Phind',
  'kagi.com': 'Kagi',
  'brave.com': 'Brave',
  'duckduckgo.com': 'DuckDuckGo',
  'grok.com': 'X/Grok',
  'x.com': 'X/Grok',
  'meta.ai': 'Meta/LLaMA',
  'doubao.com': 'ByteDance/Doubao',
};

const SITE_CONFIG = {
  'mos2es.org': {
    name: 'MO§ES™ Promo Site',
    description: 'Enterprise AI operator evaluations and performative benchmarks.',
    sitemap: 'https://mos2es.org/sitemap.xml',
    llms_txt: 'https://mos2es.org/llms.txt',
    openapi: 'https://mos2es.org/openapi.json',
    mcp: 'https://mcp.mos2es.org/mcp',
    ai_search: 'https://f8f5e9c3-29e1-4698-8866-dad70ae2bf23.search.ai.cloudflare.com/mcp',
    pages: 52,
  },
  'mos2es.com': {
    name: 'MO§ES™ Promo Site (.com)',
    description: 'Enterprise AI operator evaluations and performative benchmarks.',
    sitemap: 'https://mos2es.com/sitemap.xml',
    llms_txt: 'https://mos2es.com/llms.txt',
    openapi: 'https://mos2es.com/openapi.json',
    mcp: 'https://mcp.mos2es.org/mcp',
    ai_search: 'https://f8f5e9c3-29e1-4698-8866-dad70ae2bf23.search.ai.cloudflare.com/mcp',
    pages: 52,
  },
  'enterprise.mos2es.org': {
    name: 'MO§ES™ Enterprise Demo',
    description: 'Interactive enterprise pilot demo with real synthetic data.',
    sitemap: null,
    llms_txt: null,
    openapi: null,
    mcp: 'https://mcp.mos2es.org/mcp',
    ai_search: null,
    pages: 20,
  },
  'mcp.mos2es.org': {
    name: 'MO§ES™ MCP Server',
    description: '27-tool MCP server for AI agent integration (22 read + 5 write).',
    sitemap: null,
    llms_txt: null,
    openapi: 'https://mos2es.org/openapi.json',
    mcp: 'https://mcp.mos2es.org/mcp',
    ai_search: null,
    pages: 0,
    tools: 27,
  },
};

function detectBot(userAgent) {
  if (!userAgent) return null;
  const ua = userAgent.toLowerCase();
  for (const [bot, info] of Object.entries(AI_CRAWLERS)) {
    if (ua.includes(bot)) return { bot, ...info };
  }
  // Generic bot patterns
  if (ua.includes('bot') || ua.includes('crawler') || ua.includes('spider') || ua.includes('scraper')) {
    return { bot: 'generic', engine: 'Unknown', type: 'unknown' };
  }
  return null;
}

// Detect if a referrer URL is from an AI engine — returns engine name or null
function detectAiReferrer(referrer) {
  if (!referrer) return null;
  try {
    const host = new URL(referrer).hostname.toLowerCase();
    for (const [domain, engine] of Object.entries(AI_REFERRER_DOMAINS)) {
      if (host === domain || host.endsWith('.' + domain)) return engine;
    }
  } catch {
    // Not a valid URL — try raw match
    const lower = referrer.toLowerCase();
    for (const [domain, engine] of Object.entries(AI_REFERRER_DOMAINS)) {
      if (lower.includes(domain)) return engine;
    }
  }
  return null;
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Privacy-preserving IP hash for tracking unique visitors without storing IPs
async function sha256(str) {
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = [...new Uint8Array(hashBuffer)];
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

function jsonResponse(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Vary': 'Accept',
      ...corsHeaders(),
      ...extra,
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const host = url.hostname;

    // CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    // ─── /api/analytics/beacon — record event ───────────────────────────
    if (path === '/api/analytics/beacon' && method === 'POST') {
      return handleBeacon(request, env, host);
    }

    // ─── /api/analytics/stats — aggregated stats ────────────────────────
    if (path === '/api/analytics/stats' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleStats(request, env, queryHost, url);
    }

    // ─── /api/analytics/bots — bot/AI crawler visits ────────────────────
    if (path === '/api/analytics/bots' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleBotStats(request, env, queryHost, url);
    }

    // ─── /api/analytics/agent-trail — detailed agent provenance ─────────
    if (path === '/api/analytics/agent-trail' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleAgentTrail(request, env, queryHost, url);
    }

    // ─── /api/analytics/crawl-referral-ratio ───────────────────────────
    if (path === '/api/analytics/crawl-referral-ratio' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleCrawlReferralRatio(request, env, queryHost, url);
    }

    // ─── /api/analytics/ai-overview — AI engine visibility ──────────────
    if (path === '/api/analytics/ai-overview' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleAiOverview(request, env, queryHost);
    }

    // ─── /api/analytics/realtime — real-time counters ───────────────────
    if (path === '/api/analytics/realtime' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleRealtime(request, env, queryHost);
    }

    // ─── /api/analytics/web-vitals — Core Web Vitals ────────────────────
    if (path === '/api/analytics/web-vitals' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || host;
      return handleWebVitals(request, env, queryHost);
    }

    // ─── /dashboard — live analytics dashboard ──────────────────────────
    if (path === '/dashboard' && method === 'GET') {
      return handleDashboard(host);
    }

    // ─── /crawl-control.json — machine-readable crawl rules ─────────────
    if (path === '/crawl-control.json' && method === 'GET') {
      return handleCrawlControlJson(host);
    }

    // ─── /crawl-control — human-readable page ───────────────────────────
    if (path === '/crawl-control' && method === 'GET') {
      return handleCrawlControlPage(host);
    }

    // ─── /.well-known/agent.json — agent readiness manifest ─────────────
    if (path === '/.well-known/agent.json' && method === 'GET') {
      return handleAgentManifest(host);
    }

    // ─── /.well-known/ai-crawler-log — AI crawler self-report ───────────
    if (path === '/.well-known/ai-crawler-log' && method === 'POST') {
      return handleCrawlerSelfReport(request, env, host);
    }

    // ─── Pass through other /.well-known/agent* paths to the promo worker ─
    // The route pattern "mos2es.org/.well-known/agent*" catches these paths,
    // but they should be served by the promo worker (agent-card.json, etc.)
    if (path.startsWith('/.well-known/agent')) {
      // Fetch from the promo worker via the workers.dev URL
      const promoUrl = 'https://moses-promo.sigrank.workers.dev' + path;
      const promoResponse = await fetch(promoUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== 'GET' ? request.body : undefined,
      });
      const content = await promoResponse.text();
      return new Response(content, {
        status: promoResponse.status,
        headers: {
          'Content-Type': promoResponse.headers.get('Content-Type') || 'application/json',
          'Vary': 'Accept, Accept-Encoding',
          'Cache-Control': 'public, max-age=3600',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    // 404
    return jsonResponse({ error: 'NOT_FOUND', path }, 404);
  },
};

// ═══════════════════════════════════════════════════════════════════════
// Beacon — record a page view or agent event
// ═══════════════════════════════════════════════════════════════════════
async function handleBeacon(request, env, host) {
  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: 'INVALID_JSON' }, 400);
  }

  // Use the site field from payload for KV keys (enables cross-origin beaconing)
  // Falls back to request host for same-origin beacons
  const trackingHost = body.site || host;

  const userAgent = request.headers.get('User-Agent') || '';
  const cf = request.cf || {};
  const botInfo = detectBot(userAgent);

  const event = {
    type: body.type || 'pageview',
    path: body.path || '/',
    host: trackingHost,
    originHost: host,
    timestamp: Date.now(),
    userAgent,
    bot: botInfo?.bot || null,
    botEngine: botInfo?.engine || null,
    botType: botInfo?.type || null,
    country: cf.country || null,
    region: cf.region || null,
    city: cf.city || null,
    colo: cf.colo || null,
    referrer: body.referrer || request.headers.get('Referer') || null,
    // AI overview tracking
    aiEngine: body.aiEngine || null,
    aiQuery: body.aiQuery || null,
    aiPosition: body.aiPosition || null,
    aiCited: body.aiCited || null,
    // Core Web Vitals
    lcp: body.lcp ?? null,
    inp: body.inp ?? null,
    cls: body.cls ?? null,
    ttfb: body.ttfb ?? null,
    fid: body.fid ?? null,
  };

  // Write to Analytics Engine (time-series, SQL-queryable)
  if (env.ANALYTICS_ENGINE) {
    env.ANALYTICS_ENGINE.writeDataPoint({
      blobs: [
        event.type, event.path, event.host, event.bot || '',
        event.botEngine || '', event.country || '', event.city || '',
        event.referrer || '', event.aiEngine || '', event.aiQuery || '',
      ],
      doubles: [event.timestamp, event.aiPosition || 0, event.aiCited ? 1 : 0],
      indexes: [event.host, event.bot || 'human'],
    });
  }

  // Update KV — consolidated to minimize operations (free tier: 1000 writes/day)
  // Strategy: 1 read + 1 write for all counters, 1 read + 1 write for logs
  // = 4 operations per beacon (down from ~36)
  if (env.ANALYTICS_KV) {
    const today = new Date().toISOString().slice(0, 10);
    const aiReferrerEngine = !botInfo ? detectAiReferrer(event.referrer) : null;

    // ── Consolidated counters: 1 read + 1 write ──────────────────────
    const counterKey = `${trackingHost}:counters`;
    const counterRaw = await env.ANALYTICS_KV.get(counterKey) || '{}';
    const counters = JSON.parse(counterRaw);

    // Helper to increment nested counter paths
    function incr(...path) {
      let obj = counters;
      for (let i = 0; i < path.length - 1; i++) {
        obj[path[i]] = obj[path[i]] || {};
        obj = obj[path[i]];
      }
      const last = path[path.length - 1];
      obj[last] = (obj[last] || 0) + 1;
    }

    incr('total');
    incr('byDay', today);
    incr('byType', event.type);
    incr('byDayType', today, event.type);

    if (botInfo) {
      incr('bots', botInfo.bot);
      incr('botsByDay', today, botInfo.bot);
      incr('botsByEngine', botInfo.engine);
      incr('crawlByEngine', botInfo.engine);
      incr('crawlByEngineByDay', today, botInfo.engine);
    } else {
      incr('human');
      incr('humanByDay', today);
    }
    if (event.country) incr('byCountry', event.country);
    if (event.aiEngine) incr('aiByEngine', event.aiEngine);
    if (aiReferrerEngine) {
      incr('referralByEngine', aiReferrerEngine);
      incr('referralByEngineByDay', today, aiReferrerEngine);
    }

    // ── Consolidated logs: 1 read + 1 write ──────────────────────────
    const logKey = `${trackingHost}:logs`;
    const logRaw = await env.ANALYTICS_KV.get(logKey) || '{}';
    const logs = JSON.parse(logRaw);
    logs.botLog = logs.botLog || [];
    logs.aiOverviewLog = logs.aiOverviewLog || [];
    logs.eventLog = logs.eventLog || [];

    // Add bot visit to log
    if (botInfo) {
      logs.botLog.unshift({
        bot: botInfo.bot,
        engine: botInfo.engine,
        type: botInfo.type,
        path: event.path,
        country: event.country,
        region: event.region,
        city: event.city,
        colo: event.colo,
        asn: cf.asn || null,
        asOrganization: cf.asOrganization || null,
        referrer: event.referrer,
        userAgent: userAgent.slice(0, 500),
        acceptHeader: request.headers.get('Accept')?.slice(0, 200) || null,
        timestamp: event.timestamp,
        ipHash: request.headers.get('CF-Connecting-IP')
          ? await sha256(request.headers.get('CF-Connecting-IP').slice(0, 16))
          : null,
      });
      logs.botLog = logs.botLog.slice(0, 200);
    }

    // Add AI overview event
    if (event.aiEngine) {
      logs.aiOverviewLog.unshift({
        engine: event.aiEngine, query: event.aiQuery,
        position: event.aiPosition, cited: event.aiCited,
        path: event.path, timestamp: event.timestamp,
      });
      logs.aiOverviewLog = logs.aiOverviewLog.slice(0, 100);
    }

    // Add to event log
    logs.eventLog.unshift(event);
    logs.eventLog = logs.eventLog.slice(0, 200);

    // Write both in parallel: 2 writes total
    await Promise.all([
      env.ANALYTICS_KV.put(counterKey, JSON.stringify(counters)),
      env.ANALYTICS_KV.put(logKey, JSON.stringify(logs)),
    ]);
  }

  return jsonResponse({ success: true, recorded: true });
}

// ═══════════════════════════════════════════════════════════════════════
// Helper: load consolidated counters + logs in 2 reads
// ═══════════════════════════════════════════════════════════════════════
async function loadConsolidated(env, host) {
  const [counterRaw, logRaw] = await Promise.all([
    env.ANALYTICS_KV.get(`${host}:counters`),
    env.ANALYTICS_KV.get(`${host}:logs`),
  ]);
  return {
    counters: JSON.parse(counterRaw || '{}'),
    logs: JSON.parse(logRaw || '{}'),
  };
}

// ═══════════════════════════════════════════════════════════════════════
// Stats — aggregated analytics (2 KV reads instead of ~30)
// ═══════════════════════════════════════════════════════════════════════
async function handleStats(request, env, host, url) {
  const days = parseInt(url.searchParams.get('days') || '7', 10);
  const stats = { host, days, totals: {}, byDay: {}, byType: {}, byCountry: {}, bots: {} };

  if (!env.ANALYTICS_KV) return jsonResponse(stats);

  const { counters, logs } = await loadConsolidated(env, host);
  const today = new Date();
  const total = counters.total || 0;
  const human = counters.human || 0;
  stats.totals = { all: total, human, bots: total - human };

  // By day
  for (let i = 0; i < days; i++) {
    const d = new Date(today.getTime() - i * 86400000).toISOString().slice(0, 10);
    const dayCount = counters.byDay?.[d] || 0;
    const humanCount = counters.humanByDay?.[d] || 0;
    stats.byDay[d] = { total: dayCount, human: humanCount, bots: dayCount - humanCount };
  }

  // By type
  stats.byType = counters.byType || {};

  // By country
  stats.byCountry = counters.byCountry || {};

  // Bot log
  const botLog = logs.botLog || [];
  stats.bots.recentVisits = botLog.slice(0, 20);
  const botCounts = {};
  for (const entry of botLog) {
    botCounts[entry.bot] = (botCounts[entry.bot] || 0) + 1;
  }
  stats.bots.byBot = botCounts;

  return jsonResponse(stats);
}

// ═══════════════════════════════════════════════════════════════════════
// Bot stats — AI crawler visit detail (2 KV reads instead of ~30)
// ═══════════════════════════════════════════════════════════════════════
async function handleBotStats(request, env, host, url) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, bots: [] });

  const { counters, logs } = await loadConsolidated(env, host);
  const botLog = logs.botLog || [];
  const byBot = {};
  const byEngine = {};

  for (const entry of botLog) {
    byBot[entry.bot] = (byBot[entry.bot] || 0) + 1;
    byEngine[entry.engine] = (byEngine[entry.engine] || 0) + 1;
  }

  // Per-bot totals from consolidated counters
  const botTotals = {};
  const botsCounters = counters.bots || {};
  for (const bot of Object.keys(AI_CRAWLERS)) {
    if (botsCounters[bot]) {
      botTotals[bot] = { count: botsCounters[bot], ...AI_CRAWLERS[bot] };
    }
  }

  return jsonResponse({
    host,
    recentVisits: botLog.slice(0, 50),
    byBot,
    byEngine,
    allTimeTotals: botTotals,
    knownCrawlers: Object.keys(AI_CRAWLERS).length,
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Agent Trail — detailed agent provenance (2 KV reads instead of 1)
// ═══════════════════════════════════════════════════════════════════════
async function handleAgentTrail(request, env, host, url) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, trail: [], provenance: {} });

  const { logs } = await loadConsolidated(env, host);
  const botLog = logs.botLog || [];
  const limit = parseInt(url.searchParams.get('limit') || '100', 10);
  const filterBot = url.searchParams.get('bot');
  const filterEngine = url.searchParams.get('engine');

  let filtered = botLog;
  if (filterBot) filtered = filtered.filter(e => e.bot === filterBot);
  if (filterEngine) filtered = filtered.filter(e => e.engine === filterEngine);

  // Build provenance summaries
  const byCountry = {};
  const byAsn = {};
  const byReferrer = {};
  const byPath = {};
  const byAccept = {};
  const byCity = {};
  const uniqueIpHashes = new Set();

  for (const entry of filtered) {
    if (entry.country) byCountry[entry.country] = (byCountry[entry.country] || 0) + 1;
    if (entry.asn) {
      const key = `AS${entry.asn}${entry.asOrganization ? ' (' + entry.asOrganization + ')' : ''}`;
      byAsn[key] = (byAsn[key] || 0) + 1;
    }
    if (entry.referrer) byReferrer[entry.referrer] = (byReferrer[entry.referrer] || 0) + 1;
    if (entry.path) byPath[entry.path] = (byPath[entry.path] || 0) + 1;
    if (entry.acceptHeader) {
      const acceptShort = entry.acceptHeader.includes('text/markdown') ? 'text/markdown'
        : entry.acceptHeader.includes('application/json') ? 'application/json'
        : entry.acceptHeader.includes('text/html') ? 'text/html'
        : entry.acceptHeader.slice(0, 50);
      byAccept[acceptShort] = (byAccept[acceptShort] || 0) + 1;
    }
    if (entry.city) byCity[entry.city] = (byCity[entry.city] || 0) + 1;
    if (entry.ipHash) uniqueIpHashes.add(entry.ipHash);
  }

  return jsonResponse({
    host,
    totalVisits: filtered.length,
    uniqueVisitors: uniqueIpHashes.size,
    trail: filtered.slice(0, limit),
    provenance: {
      byCountry: sortObject(byCountry),
      byCity: sortObject(byCity),
      byAsn: sortObject(byAsn),
      byReferrer: sortObject(byReferrer),
      byPath: sortObject(byPath),
      byAcceptType: sortObject(byAccept),
    },
  });
}

function sortObject(obj) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1]).reduce((r, [k, v]) => { r[k] = v; return r; }, {});
}

// ═══════════════════════════════════════════════════════════════════════
// Crawl-to-Referral Ratio (2 KV reads instead of ~480)
// ═══════════════════════════════════════════════════════════════════════
async function handleCrawlReferralRatio(request, env, host, url) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, engines: [], summary: {} });

  const days = parseInt(url.searchParams.get('days') || '7', 10);
  const today = new Date();
  const { counters } = await loadConsolidated(env, host);

  // Collect all known engines from both crawler and referrer domains
  const allEngines = new Set([
    ...Object.values(AI_CRAWLERS).map(c => c.engine),
    ...Object.values(AI_REFERRER_DOMAINS),
  ]);

  const crawlByEngine = counters.crawlByEngine || {};
  const crawlByEngineByDay = counters.crawlByEngineByDay || {};
  const referralByEngine = counters.referralByEngine || {};
  const referralByEngineByDay = counters.referralByEngineByDay || {};

  const engines = [];

  for (const engine of allEngines) {
    const crawlTotal = crawlByEngine[engine] || 0;
    const referralTotal = referralByEngine[engine] || 0;

    // Per-day breakdown for the requested period
    const byDay = {};
    let periodCrawls = 0;
    let periodReferrals = 0;
    for (let i = 0; i < days; i++) {
      const d = new Date(today.getTime() - i * 86400000).toISOString().slice(0, 10);
      const dayCrawls = crawlByEngineByDay?.[d]?.[engine] || 0;
      const dayReferrals = referralByEngineByDay?.[d]?.[engine] || 0;
      if (dayCrawls > 0 || dayReferrals > 0) {
        byDay[d] = { crawls: dayCrawls, referrals: dayReferrals };
        periodCrawls += dayCrawls;
        periodReferrals += dayReferrals;
      }
    }

    // Only include engines with activity
    if (crawlTotal > 0 || referralTotal > 0) {
      const ratio = referralTotal > 0 ? (crawlTotal / referralTotal).toFixed(2) : '∞';
      const periodRatio = periodReferrals > 0 ? (periodCrawls / periodReferrals).toFixed(2) : '∞';
      engines.push({
        engine,
        allTime: {
          crawls: crawlTotal,
          referrals: referralTotal,
          ratio: parseFloat(ratio),
          ratioLabel: ratio,
        },
        lastDays: {
          days,
          crawls: periodCrawls,
          referrals: periodReferrals,
          ratio: parseFloat(periodRatio),
          ratioLabel: periodRatio,
        },
        byDay: sortObject(byDay),
      });
    }
  }

  // Sort by all-time crawls descending
  engines.sort((a, b) => b.allTime.crawls - a.allTime.crawls);

  // Summary
  const totalCrawls = engines.reduce((s, e) => s + e.allTime.crawls, 0);
  const totalReferrals = engines.reduce((s, e) => s + e.allTime.referrals, 0);
  const periodCrawlsTotal = engines.reduce((s, e) => s + e.lastDays.crawls, 0);
  const periodReferralsTotal = engines.reduce((s, e) => s + e.lastDays.referrals, 0);

  return jsonResponse({
    host,
    days,
    generated: new Date().toISOString(),
    engines,
    summary: {
      totalCrawls,
      totalReferrals,
      overallRatio: totalReferrals > 0 ? parseFloat((totalCrawls / totalReferrals).toFixed(2)) : null,
      overallRatioLabel: totalReferrals > 0 ? (totalCrawls / totalReferrals).toFixed(2) : '∞',
      periodCrawls: periodCrawlsTotal,
      periodReferrals: periodReferralsTotal,
      periodRatio: periodReferralsTotal > 0 ? parseFloat((periodCrawlsTotal / periodReferralsTotal).toFixed(2)) : null,
      periodRatioLabel: periodReferralsTotal > 0 ? (periodCrawlsTotal / periodReferralsTotal).toFixed(2) : '∞',
      enginesTracked: engines.length,
    },
  });
}

// ═══════════════════════════════════════════════════════════════════════
// AI Overview (2 KV reads instead of ~30)
// ═══════════════════════════════════════════════════════════════════════
async function handleAiOverview(request, env, host) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, aiOverviews: [] });

  const { counters, logs } = await loadConsolidated(env, host);
  const aiLog = logs.aiOverviewLog || [];
  const byEngine = {};
  const byQuery = {};

  for (const entry of aiLog) {
    byEngine[entry.engine] = (byEngine[entry.engine] || 0) + 1;
    if (entry.query) {
      byQuery[entry.query] = (byQuery[entry.query] || 0) + 1;
    }
  }

  // Check which known AI crawlers have visited (from consolidated counters)
  const crawlerPresence = {};
  const botsCounters = counters.bots || {};
  for (const [bot, info] of Object.entries(AI_CRAWLERS)) {
    if (botsCounters[bot] && botsCounters[bot] > 0) {
      crawlerPresence[info.engine] = { bot, visits: botsCounters[bot], type: info.type };
    }
  }

  return jsonResponse({
    host,
    aiOverviewEvents: aiLog.slice(0, 50),
    byEngine,
    byQuery,
    crawlerPresence,
    readinessScore: Object.keys(crawlerPresence).length,
    totalKnownEngines: new Set(Object.values(AI_CRAWLERS).map(c => c.engine)).size,
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Realtime — current counters (1 KV read instead of 4)
// ═══════════════════════════════════════════════════════════════════════
async function handleRealtime(request, env, host) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, realtime: {} });

  const today = new Date().toISOString().slice(0, 10);
  const { counters } = await loadConsolidated(env, host);
  const totalAllTime = counters.total || 0;
  const humanAllTime = counters.human || 0;
  const todayTotal = counters.byDay?.[today] || 0;
  const todayHuman = counters.humanByDay?.[today] || 0;

  return jsonResponse({
    host,
    date: today,
    realtime: {
      totalAllTime,
      humanAllTime,
      todayTotal,
      todayHuman,
      todayBots: todayTotal - todayHuman,
    },
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Core Web Vitals (1 KV read instead of 2)
// ═══════════════════════════════════════════════════════════════════════
async function handleWebVitals(request, env, host) {
  if (!env.ANALYTICS_KV) return jsonResponse({ host, webVitals: { samples: 0, metrics: {} } });

  // Read the recent events log from consolidated logs
  const { logs } = await loadConsolidated(env, host);
  const eventLog = logs.eventLog || [];
  const vitalsEvents = eventLog.filter(e => e.type === 'web_vitals' && e.lcp != null);

  if (vitalsEvents.length === 0) {
    return jsonResponse({
      host,
      webVitals: {
        samples: 0,
        metrics: {},
        message: 'No Core Web Vitals data yet. Data is collected from real visitors via the analytics beacon.',
      },
    });
  }

  // Compute percentiles (p50, p75, p95)
  function percentile(arr, p) {
    if (arr.length === 0) return null;
    const sorted = [...arr].sort((a, b) => a - b);
    const idx = Math.ceil(sorted.length * p) - 1;
    return sorted[Math.max(0, idx)];
  }

  const lcp = vitalsEvents.map(e => e.lcp).filter(v => v != null);
  const inp = vitalsEvents.map(e => e.inp).filter(v => v != null);
  const cls = vitalsEvents.map(e => e.cls).filter(v => v != null);
  const ttfb = vitalsEvents.map(e => e.ttfb).filter(v => v != null);

  const metrics = {};
  for (const [name, values, thresholds] of [
    ['lcp', lcp, [2500, 4000]],
    ['inp', inp, [200, 500]],
    ['cls', cls, [0.1, 0.25]],
    ['ttfb', ttfb, [800, 1800]],
  ]) {
    if (values.length > 0) {
      metrics[name] = {
        samples: values.length,
        p50: percentile(values, 0.5),
        p75: percentile(values, 0.75),
        p95: percentile(values, 0.95),
        good: thresholds[0],
        poor: thresholds[1],
        rating: percentile(values, 0.75) <= thresholds[0] ? 'good' : percentile(values, 0.75) <= thresholds[1] ? 'needs-improvement' : 'poor',
      };
    }
  }

  return jsonResponse({
    host,
    webVitals: {
      samples: vitalsEvents.length,
      metrics,
      lastUpdated: vitalsEvents[0]?.timestamp || null,
    },
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Crawl Control — machine-readable
// ═══════════════════════════════════════════════════════════════════════
function handleCrawlControlJson(host) {
  const config = SITE_CONFIG[host] || SITE_CONFIG['mos2es.org'];
  return jsonResponse({
    site: host,
    version: '1.0',
    generated: new Date().toISOString(),
    crawlPolicy: {
      default: 'allow',
      aiTraining: 'allow',
      aiSearch: 'allow',
      aiAgents: 'allow',
      rateLimit: '120req/min',
    },
    allowedCrawlers: Object.entries(AI_CRAWLERS).map(([bot, info]) => ({
      userAgent: bot,
      engine: info.engine,
      type: info.type,
      policy: 'allow',
    })),
    disallowedPaths: [
      '/api/analytics/*',
      '/crawl-control*',
    ],
    sitemap: config.sitemap,
    llms_txt: config.llms_txt,
    openapi: config.openapi,
    mcp: config.mcp,
    ai_search: config.ai_search,
    agentManifest: `https://${host}/.well-known/agent.json`,
    beacon: `https://${host}/api/analytics/beacon`,
    selfReport: `https://${host}/.well-known/ai-crawler-log`,
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Crawl Control — human-readable
// ═══════════════════════════════════════════════════════════════════════
function handleCrawlControlPage(host) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crawl Control — ${host}</title>
<style>
body{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.6}
h1{font-size:1.5rem}h2{font-size:1.2rem;margin-top:2rem}
table{width:100%;border-collapse:collapse;margin:1rem 0}
th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e0e0e0}
.allow{color:green}.deny{color:red}
code{background:#f5f5f5;padding:0.2rem 0.4rem;border-radius:3px}
</style>
</head>
<body>
<h1>Crawl Control — ${host}</h1>
<p>Machine-readable config: <a href="/crawl-control.json"><code>/crawl-control.json</code></a></p>
<h2>Policy</h2>
<table>
<tr><th>Category</th><th>Policy</th></tr>
<tr><td>Default</td><td class="allow">Allow</td></tr>
<tr><td>AI Training</td><td class="allow">Allow</td></tr>
<tr><td>AI Search</td><td class="allow">Allow</td></tr>
<tr><td>AI Agents</td><td class="allow">Allow</td></tr>
<tr><td>Rate Limit</td><td>120 req/min</td></tr>
</table>
<h2>Allowed AI Crawlers (${Object.keys(AI_CRAWLERS).length})</h2>
<table>
<tr><th>User-Agent</th><th>Engine</th><th>Type</th><th>Policy</th></tr>
${Object.entries(AI_CRAWLERS).map(([bot, info]) =>
  `<tr><td>${bot}</td><td>${info.engine}</td><td>${info.type}</td><td class="allow">Allow</td></tr>`
).join('')}
</table>
<h2>Agent Endpoints</h2>
<ul>
<li><a href="/.well-known/agent.json"><code>/.well-known/agent.json</code></a> — Agent readiness manifest</li>
<li><a href="/crawl-control.json"><code>/crawl-control.json</code></a> — Machine-readable crawl rules</li>
<li><code>/api/analytics/beacon</code> — Event beacon (POST)</li>
<li><code>/.well-known/ai-crawler-log</code> — AI crawler self-report (POST)</li>
</ul>
</body>
</html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}

// ═══════════════════════════════════════════════════════════════════════
// Agent Readiness Manifest
// ═══════════════════════════════════════════════════════════════════════
function handleAgentManifest(host) {
  const config = SITE_CONFIG[host] || SITE_CONFIG['mos2es.org'];
  return jsonResponse({
    schema: 'agent-readiness/v1',
    site: host,
    name: config.name,
    description: config.description,
    generated: new Date().toISOString(),
    capabilities: {
      searchable: config.sitemap !== null,
      llmsTxt: config.llms_txt !== null,
      openApi: config.openapi !== null,
      mcpServer: config.mcp !== null,
      aiSearch: config.ai_search !== null,
      crawlControl: true,
      analytics: true,
    },
    endpoints: {
      sitemap: config.sitemap,
      llms_txt: config.llms_txt,
      openapi: config.openapi,
      mcp: config.mcp,
      ai_search: config.ai_search,
      crawl_control: `https://${host}/crawl-control.json`,
      agent_manifest: `https://${host}/.well-known/agent.json`,
      analytics_beacon: `https://${host}/api/analytics/beacon`,
      analytics_stats: `https://${host}/api/analytics/stats`,
      analytics_bots: `https://${host}/api/analytics/bots`,
      analytics_ai_overview: `https://${host}/api/analytics/ai-overview`,
      analytics_realtime: `https://${host}/api/analytics/realtime`,
      crawler_self_report: `https://${host}/.well-known/ai-crawler-log`,
    },
    crawlPolicy: {
      default: 'allow',
      aiTraining: 'allow',
      aiSearch: 'allow',
      aiAgents: 'allow',
    },
    contentStats: {
      pages: config.pages,
      tools: config.tools || 0,
    },
    aiCrawlerAllowList: Object.keys(AI_CRAWLERS),
  });
}

// ═══════════════════════════════════════════════════════════════════════
// AI Crawler Self-Report — crawlers can POST their visit
// ═══════════════════════════════════════════════════════════════════════
async function handleCrawlerSelfReport(request, env, host) {
  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: 'INVALID_JSON' }, 400);
  }

  const userAgent = request.headers.get('User-Agent') || '';
  const botInfo = detectBot(userAgent) || detectBot(body.userAgent || '');

  if (!botInfo) {
    return jsonResponse({ error: 'UNKNOWN_CRAWLER', message: 'Could not identify crawler from User-Agent' }, 400);
  }

  const event = {
    type: 'crawler_self_report',
    bot: botInfo.bot,
    engine: botInfo.engine,
    crawlerType: botInfo.type,
    path: body.path || '/',
    pagesCrawled: body.pagesCrawled || 1,
    purpose: body.purpose || 'unknown',
    timestamp: Date.now(),
    host,
  };

  // Write to Analytics Engine
  if (env.ANALYTICS_ENGINE) {
    env.ANALYTICS_ENGINE.writeDataPoint({
      blobs: [event.type, event.path, event.host, event.bot, event.engine, event.purpose, ''],
      doubles: [event.timestamp, event.pagesCrawled, 0],
      indexes: [event.host, event.bot],
    });
  }

  // Update KV
  if (env.ANALYTICS_KV) {
    const logKey = `${host}:bot-log`;
    const logRaw = await env.ANALYTICS_KV.get(logKey) || '[]';
    const log = JSON.parse(logRaw);
    log.unshift({
      bot: event.bot, engine: event.engine, type: event.crawlerType,
      path: event.path, purpose: event.purpose, pagesCrawled: event.pagesCrawled,
      selfReported: true, timestamp: event.timestamp,
    });
    await env.ANALYTICS_KV.put(logKey, JSON.stringify(log.slice(0, 100)));

    const countKey = `${host}:bots:${event.bot}`;
    const current = parseInt(await env.ANALYTICS_KV.get(countKey) || '0', 10);
    await env.ANALYTICS_KV.put(countKey, String(current + (event.pagesCrawled || 1)));
  }

  return jsonResponse({ success: true, crawler: botInfo.bot, engine: botInfo.engine });
}

// ═══════════════════════════════════════════════════════════════════════
// Dashboard — live HTML analytics dashboard
// ═══════════════════════════════════════════════════════════════════════
function handleDashboard(host) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics Dashboard — ${host}</title>
<meta name="robots" content="noindex,nofollow">
<style>
:root {
  --bg: #0d1117; --card: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --red: #f85149; --yellow: #d29922; --purple: #bc8cff;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 1rem; max-width: 1200px; margin: 0 auto; }
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; margin: 1.5rem 0 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.grid { display: grid; gap: 0.75rem; }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
.grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
.stat { text-align: center; }
.stat .num { font-size: 1.8rem; font-weight: 700; }
.stat .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }
.stat.human .num { color: var(--green); }
.stat.bot .num { color: var(--yellow); }
.stat.total .num { color: var(--accent); }
.stat.ai .num { color: var(--purple); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
.badge.green { background: rgba(63,185,80,0.2); color: var(--green); }
.badge.yellow { background: rgba(210,153,34,0.2); color: var(--yellow); }
.badge.blue { background: rgba(88,166,255,0.2); color: var(--accent); }
.badge.purple { background: rgba(188,140,255,0.2); color: var(--purple); }
.badge.red { background: rgba(248,81,73,0.2); color: var(--red); }
.bar-chart { display: flex; align-items: flex-end; gap: 4px; height: 80px; margin-top: 0.5rem; }
.bar { flex: 1; background: var(--accent); border-radius: 3px 3px 0 0; min-height: 2px; position: relative; transition: height 0.3s; }
.bar:hover { background: var(--purple); }
.bar-label { position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); font-size: 0.6rem; color: var(--muted); }
.bar-container { padding-bottom: 1.5rem; }
.empty { color: var(--muted); font-style: italic; padding: 1rem 0; }
.refresh { position: fixed; top: 1rem; right: 1rem; background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.refresh:hover { border-color: var(--accent); }
.loading { opacity: 0.5; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.endpoints { font-size: 0.75rem; }
.endpoints code { background: var(--bg); padding: 0.2rem 0.4rem; border-radius: 3px; color: var(--green); }
</style>
</head>
<body>
<button class="refresh" onclick="loadAll()">Refresh</button>
<h1>MO\u00a7ES\u2122 Analytics Dashboard</h1>
<p class="subtitle">${host} \u2014 live agent + visitor + crawler monitoring</p>

<h2>Realtime</h2>
<div class="grid grid-4" id="realtime">
  <div class="card stat total"><div class="num" id="rt-total">-</div><div class="label">Total Today</div></div>
  <div class="card stat human"><div class="num" id="rt-human">-</div><div class="label">Human Today</div></div>
  <div class="card stat bot"><div class="num" id="rt-bots">-</div><div class="label">Bots Today</div></div>
  <div class="card stat total"><div class="num" id="rt-all">-</div><div class="label">All Time</div></div>
</div>

<h2>7-Day Activity</h2>
<div class="card bar-container">
  <div class="bar-chart" id="bar-chart"></div>
</div>

<h2>AI Crawler Presence</h2>
<div class="card" id="bots-card">
  <table>
    <thead><tr><th>Engine</th><th>Bot</th><th>Type</th><th>Visits</th><th>Last Seen</th></tr></thead>
    <tbody id="bots-table"><tr><td colspan="5" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>AI Overview Citations</h2>
<div class="card" id="ai-card">
  <table>
    <thead><tr><th>Engine</th><th>Query</th><th>Position</th><th>Cited</th><th>Time</th></tr></thead>
    <tbody id="ai-table"><tr><td colspan="5" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>By Type</h2>
<div class="card" id="types-card">
  <table>
    <thead><tr><th>Event Type</th><th>Count</th></tr></thead>
    <tbody id="types-table"><tr><td colspan="2" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>Agent Readiness</h2>
<div class="card" id="readiness-card">
  <div id="readiness" class="empty">Loading...</div>
</div>

<h2>API Endpoints</h2>
<div class="card endpoints">
  <code>GET /api/analytics/realtime</code> \u2014 current counters<br>
  <code>GET /api/analytics/stats?days=7</code> \u2014 aggregated stats<br>
  <code>GET /api/analytics/bots</code> \u2014 AI crawler visits<br>
  <code>GET /api/analytics/ai-overview</code> \u2014 AI engine visibility<br>
  <code>POST /api/analytics/beacon</code> \u2014 record event<br>
  <code>GET /.well-known/agent.json</code> \u2014 agent manifest<br>
  <code>GET /crawl-control.json</code> \u2014 crawl rules<br>
  <code>GET /dashboard</code> \u2014 this page
</div>

<script>
async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    return await r.json();
  } catch(e) { return null; }
}

function timeAgo(ts) {
  if (!ts) return '-';
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s/60) + 'm ago';
  if (s < 86400) return Math.floor(s/3600) + 'h ago';
  return Math.floor(s/86400) + 'd ago';
}

async function loadRealtime() {
  const d = await fetchJSON('/api/analytics/realtime');
  if (!d || !d.realtime) return;
  const r = d.realtime;
  document.getElementById('rt-total').textContent = r.todayTotal;
  document.getElementById('rt-human').textContent = r.todayHuman;
  document.getElementById('rt-bots').textContent = r.todayBots;
  document.getElementById('rt-all').textContent = r.totalAllTime;
}

async function loadStats() {
  const d = await fetchJSON('/api/analytics/stats?days=7');
  if (!d || !d.byDay) return;
  const days = Object.entries(d.byDay).sort();
  const max = Math.max(...days.map(([,v]) => v.total), 1);
  const chart = document.getElementById('bar-chart');
  chart.innerHTML = days.map(([date, v]) => {
    const h = (v.total / max) * 70;
    const label = date.slice(5);
    return '<div class="bar" style="height:' + h + 'px" title="' + label + ': ' + v.total + ' (H:' + v.human + ' B:' + v.bots + ')"><span class="bar-label">' + label + '</span></div>';
  }).join('');

  if (d.byType) {
    const types = Object.entries(d.byType).sort((a,b) => b[1] - a[1]);
    document.getElementById('types-table').innerHTML = types.length
      ? types.map(([t,c]) => '<tr><td><span class="badge blue">' + t + '</span></td><td>' + c + '</td></tr>').join('')
      : '<tr><td colspan="2" class="empty">No events yet</td></tr>';
  }
}

async function loadBots() {
  const d = await fetchJSON('/api/analytics/bots');
  if (!d) return;
  const visits = d.recentVisits || [];
  const totals = d.allTimeTotals || {};
  const rows = [];
  for (const [bot, info] of Object.entries(totals)) {
    const lastVisit = visits.find(v => v.bot === bot);
    rows.push('<tr><td><strong>' + info.engine + '</strong></td><td>' + bot + '</td><td><span class="badge ' + (info.type === 'training' ? 'yellow' : 'blue') + '">' + info.type + '</span></td><td>' + info.count + '</td><td>' + (lastVisit ? timeAgo(lastVisit.timestamp) : '-') + '</td></tr>');
  }
  if (rows.length === 0 && visits.length > 0) {
    for (const v of visits.slice(0, 10)) {
      rows.push('<tr><td><strong>' + v.engine + '</strong></td><td>' + v.bot + '</td><td><span class="badge ' + (v.type === 'training' ? 'yellow' : 'blue') + '">' + v.type + '</span></td><td>1</td><td>' + timeAgo(v.timestamp) + '</td></tr>');
    }
  }
  document.getElementById('bots-table').innerHTML = rows.length
    ? rows.join('')
    : '<tr><td colspan="5" class="empty">No AI crawlers detected yet</td></tr>';
}

async function loadAiOverview() {
  const d = await fetchJSON('/api/analytics/ai-overview');
  if (!d) return;
  const events = d.aiOverviewEvents || [];
  const rows = events.slice(0, 20).map(e => {
    const cited = e.cited ? '<span class="badge green">Yes</span>' : '<span class="badge red">No</span>';
    return '<tr><td><strong>' + e.engine + '</strong></td><td>' + (e.query || '-') + '</td><td>' + (e.position || '-') + '</td><td>' + cited + '</td><td>' + timeAgo(e.timestamp) + '</td></tr>';
  });
  document.getElementById('ai-table').innerHTML = rows.length
    ? rows.join('')
    : '<tr><td colspan="5" class="empty">No AI overview events yet</td></tr>';

  const presence = d.crawlerPresence || {};
  const score = d.readinessScore || 0;
  const total = d.totalKnownEngines || 18;
  const pct = Math.round((score / total) * 100);
  const engines = Object.entries(presence).map(([engine, info]) =>
    '<span class="badge ' + (info.type === 'training' ? 'yellow' : 'blue') + '">' + engine + ' (' + info.visits + ')</span>'
  ).join(' ');
  document.getElementById('readiness').innerHTML =
    '<div style="font-size:1.5rem;font-weight:700;margin-bottom:0.5rem">' + pct + '% <span style="font-size:0.85rem;color:var(--muted)">(' + score + '/' + total + ' engines)</span></div>' +
    '<div>' + (engines || '<span class="empty">No AI engines have crawled this site yet</span>') + '</div>';
}

async function loadAll() {
  document.body.classList.add('loading');
  await Promise.all([loadRealtime(), loadStats(), loadBots(), loadAiOverview()]);
  document.body.classList.remove('loading');
}

loadAll();
setInterval(loadAll, 120000);
</script>
</body>
</html>`;
  return new Response(html, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}
