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

    // ─── /api/analytics/mcp — MCP server usage stats ───────────────────
    if (path === '/api/analytics/mcp' && method === 'GET') {
      const queryHost = url.searchParams.get('host') || 'mcp.mos2es.org';
      return handleMcpStats(request, env, queryHost, url);
    }

    // ─── /api/analytics/cloudflare — proxy to CF GraphQL Analytics API ──
    if (path === '/api/analytics/cloudflare' && method === 'GET') {
      return handleCloudflareAnalytics(request, env, url);
    }

    // ─── /dashboard — live analytics dashboard ──────────────────────────
    if (path === '/dashboard' && method === 'GET') {
      return handleDashboard(host);
    }

    // ─── /dashboard/cloudflare — Cloudflare-powered analytics dashboard ─
    if (path === '/dashboard/cloudflare' && method === 'GET') {
      return handleCloudflareDashboard(host);
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

  const userAgent = body.userAgent || request.headers.get('User-Agent') || '';
  const cf = request.cf || {};

  // Bot detection: use payload-provided bot info (from server-side detection)
  // or fall back to detecting from the user agent
  const botInfo = body.bot
    ? { bot: body.bot, engine: body.engine || 'Unknown', type: body.botType || 'unknown' }
    : detectBot(userAgent);

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
    // Use payload-provided geo data (from server-side detection) or fall back to request.cf
    country: body.country || cf.country || null,
    region: body.region || cf.region || null,
    city: body.city || cf.city || null,
    colo: body.colo || cf.colo || null,
    asn: body.asn || cf.asn || null,
    asOrganization: body.asOrganization || cf.asOrganization || null,
    acceptHeader: body.acceptHeader || null,
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
  // Strategy: 1 read + 1 write for combined counters+logs (single put)
  // = 2 operations per beacon (down from 4)
  // Throttle: skip KV writes for ~1 in 3 bot crawls to stay under daily write limit.
  // Always write for human + MCP traffic (more valuable, lower volume).
  if (env.ANALYTICS_KV) {
    if (botInfo && Math.random() < 0.33) {
      // Skip KV write for this bot crawl — counters will be slightly undercounted
      // but we stay under the 1000 writes/day free tier limit
      return jsonResponse({ success: true, recorded: true, kvSkipped: true });
    }
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
    // MCP-specific tracking
    if (body.rpcMethod) {
      incr('mcpByMethod', body.rpcMethod);
      incr('mcpByMethodByDay', today, body.rpcMethod);
    }
    if (body.toolName) {
      incr('mcpByTool', body.toolName);
      incr('mcpByToolByDay', today, body.toolName);
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
        asn: event.asn || cf.asn || null,
        asOrganization: event.asOrganization || cf.asOrganization || null,
        referrer: event.referrer,
        userAgent: userAgent.slice(0, 500),
        acceptHeader: event.acceptHeader || request.headers.get('Accept')?.slice(0, 200) || null,
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

    // Write combined: 1 write total (counters + logs in a single KV value)
    await env.ANALYTICS_KV.put(`${trackingHost}:data`, JSON.stringify({ counters, logs }));
    // Also update legacy keys for backward compat (1 extra write, but only for human/MCP)
    if (!botInfo) {
      await env.ANALYTICS_KV.put(counterKey, JSON.stringify(counters));
    }
  }

  return jsonResponse({ success: true, recorded: true });
}

// ═══════════════════════════════════════════════════════════════════════
// Helper: load consolidated counters + logs in 2 reads
// ═══════════════════════════════════════════════════════════════════════
async function loadConsolidated(env, host) {
  // Try combined key first (new format), fall back to legacy split keys
  const combinedRaw = await env.ANALYTICS_KV.get(`${host}:data`);
  if (combinedRaw) {
    const combined = JSON.parse(combinedRaw);
    return {
      counters: combined.counters || {},
      logs: combined.logs || {},
    };
  }
  // Legacy: read from separate keys
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
// MCP Server Usage Stats
// ═══════════════════════════════════════════════════════════════════════
async function handleMcpStats(request, env, host, url) {
  const days = parseInt(url.searchParams.get('days') || '7', 10);
  const stats = { host, days, totals: {}, byMethod: {}, byTool: {}, byDay: {} };

  if (!env.ANALYTICS_KV) return jsonResponse(stats);

  const { counters, logs } = await loadConsolidated(env, host);
  const today = new Date();

  // MCP request totals
  const mcpTotal = counters.byType?.mcp_request || 0;
  stats.totals = { mcpRequests: mcpTotal };

  // By RPC method
  stats.byMethod = counters.mcpByMethod || {};

  // By tool name
  stats.byTool = counters.mcpByTool || {};

  // By day
  for (let i = 0; i < days; i++) {
    const d = new Date(today.getTime() - i * 86400000).toISOString().slice(0, 10);
    const dayCount = counters.byDayType?.[d]?.mcp_request || 0;
    const methods = counters.mcpByMethodByDay?.[d] || {};
    const tools = counters.mcpByToolByDay?.[d] || {};
    stats.byDay[d] = { total: dayCount, byMethod: methods, byTool: tools };
  }

  // Recent MCP requests from event log
  const eventLog = logs.eventLog || [];
  stats.recentRequests = eventLog
    .filter(e => e.type === 'mcp_request')
    .slice(0, 50)
    .map(e => ({
      timestamp: e.timestamp,
      path: e.path,
      country: e.country,
      userAgent: (e.userAgent || '').slice(0, 100),
    }));

  return jsonResponse(stats);
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

  // Update KV — throttle to stay under free tier limit
  if (env.ANALYTICS_KV) {
    // Skip 1 in 3 crawler self-reports to conserve KV writes
    if (Math.random() < 0.33) {
      return jsonResponse({ success: true, crawler: botInfo.bot, engine: botInfo.engine, kvSkipped: true });
    }
    const logKey = `${host}:bot-log`;
    const logRaw = await env.ANALYTICS_KV.get(logKey) || '[]';
    const log = JSON.parse(logRaw);
    log.unshift({
      bot: event.bot, engine: event.engine, type: event.crawlerType,
      path: event.path, purpose: event.purpose, pagesCrawled: event.pagesCrawled,
      selfReported: true, timestamp: event.timestamp,
    });
    await env.ANALYTICS_KV.put(logKey, JSON.stringify(log.slice(0, 100)));
  }

  return jsonResponse({ success: true, crawler: botInfo.bot, engine: botInfo.engine });
}

// ═══════════════════════════════════════════════════════════════════════
// Cloudflare GraphQL Analytics proxy — queries CF's own analytics API
// Uses account-level analytics endpoint (Account Analytics Read permission)
// ═══════════════════════════════════════════════════════════════════════
const ACCOUNT_TAG = '8251078af351cd5b19cb73a3435e446f';

async function handleCloudflareAnalytics(request, env, url) {
  const days = parseInt(url.searchParams.get('days') || '7', 10);

  // Date range
  const until = new Date();
  const since = new Date(until.getTime() - days * 86400000);
  const sinceStr = since.toISOString().slice(0, 10);
  const untilStr = until.toISOString().slice(0, 10);

  const token = env.CF_API_TOKEN;
  if (!token) {
    return jsonResponse({
      error: 'CF_API_TOKEN not configured. Run: wrangler secret put CF_API_TOKEN',
    }, 503);
  }

  // Query zone-level HTTP analytics for all zones in parallel
  // Falls back to wrangler OAuth token if CF_API_TOKEN doesn't have analytics permission
  const ALL_ZONES = [
    { tag: 'd3fa790d740b94fea2395cd6348162fc', name: 'mos2es.org' },
    { tag: '7bbc2a090617046b13658ac7f9651dcb', name: 'mos2es.com' },
    { tag: '451ccf3ac9ae20feb61820442a6233b8', name: 'sigeconomy.com' },
  ];

  const zonePromises = ALL_ZONES.map(async (zone) => {
    const query = `query {
      viewer {
        zones(filter: {zoneTag: "${zone.tag}"}) {
          httpRequests1dGroups(limit: ${days}, filter: {date_geq: "${sinceStr}", date_leq: "${untilStr}"}) {
            dimensions { date }
            sum {
              requests
              pageViews
              cachedRequests
              threats
              bytes
              countryMap { clientCountryName requests }
              responseStatusMap { edgeResponseStatus requests }
            }
            uniq { uniques }
          }
        }
      }
    }`;

    try {
      const resp = await fetch('https://api.cloudflare.com/client/v4/graphql', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await resp.json();
      if (data.errors) return { zone: zone.name, error: data.errors, groups: [] };
      const zones = data?.data?.viewer?.zones || [];
      const groups = zones[0]?.httpRequests1dGroups || [];
      return { zone: zone.name, groups };
    } catch (e) {
      return { zone: zone.name, error: e.message, groups: [] };
    }
  });

  const zoneResults = await Promise.all(zonePromises);

  // Check if all zones returned errors (token doesn't have permission)
  const allErrored = zoneResults.every(zr => zr.error);
  if (allErrored) {
    return jsonResponse({
      error: 'CF_API_TOKEN does not have Zone Analytics Read permission',
      hint: 'Go to https://dash.cloudflare.com/profile/api-tokens, edit your token, and add: Zone → Analytics → Read for All zones. Or create a new token with that permission.',
      details: zoneResults[0]?.error,
    }, 403);
  }

  // Per-zone summary
  const perZone = zoneResults.map(zr => {
    const groups = zr.groups || [];
    const reqs = groups.reduce((s, g) => s + g.sum.requests, 0);
    const cached = groups.reduce((s, g) => s + g.sum.cachedRequests, 0);
    const pvs = groups.reduce((s, g) => s + g.sum.pageViews, 0);
    const uniques = groups.reduce((s, g) => s + g.uniq.uniques, 0);
    const threats = groups.reduce((s, g) => s + g.sum.threats, 0);
    const bytes = groups.reduce((s, g) => s + g.sum.bytes, 0);
    return {
      zone: zr.zone,
      requests: reqs,
      pageViews: pvs,
      cachedRequests: cached,
      cacheRatio: reqs ? (cached / reqs * 100).toFixed(1) : 0,
      uniques,
      threats,
      bytes,
      error: zr.error,
    };
  });

  // Aggregate daily data across all zones
  const dailyMap = {};
  const countryAgg = {};
  const statusAgg = {};

  for (const zr of zoneResults) {
    for (const g of (zr.groups || [])) {
      const date = g.dimensions.date;
      if (!dailyMap[date]) {
        dailyMap[date] = { date, requests: 0, pageViews: 0, cachedRequests: 0, threats: 0, bytes: 0, uniques: 0, countries: {}, statusCodes: {} };
      }
      const d = dailyMap[date];
      d.requests += g.sum.requests;
      d.pageViews += g.sum.pageViews;
      d.cachedRequests += g.sum.cachedRequests;
      d.threats += g.sum.threats;
      d.bytes += g.sum.bytes;
      d.uniques += g.uniq.uniques;

      for (const c of (g.sum.countryMap || [])) {
        d.countries[c.clientCountryName] = (d.countries[c.clientCountryName] || 0) + c.requests;
        countryAgg[c.clientCountryName] = (countryAgg[c.clientCountryName] || 0) + c.requests;
      }
      for (const s of (g.sum.responseStatusMap || [])) {
        const code = s.edgeResponseStatus;
        d.statusCodes[code] = (d.statusCodes[code] || 0) + s.requests;
        statusAgg[code] = (statusAgg[code] || 0) + s.requests;
      }
    }
  }

  const daily = Object.values(dailyMap).sort((a, b) => a.date.localeCompare(b.date)).map(d => ({
    ...d,
    cacheRatio: d.requests ? (d.cachedRequests / d.requests * 100).toFixed(1) : 0,
    countries: Object.entries(d.countries).sort((a,b) => b[1] - a[1]).slice(0, 10).map(([country, requests]) => ({ country, requests })),
    statusCodes: Object.entries(d.statusCodes).sort((a,b) => b[1] - a[1]).map(([code, requests]) => ({ code: parseInt(code), requests })),
  }));

  // Totals across all zones
  const totals = {
    requests: daily.reduce((s, d) => s + d.requests, 0),
    pageViews: daily.reduce((s, d) => s + d.pageViews, 0),
    cachedRequests: daily.reduce((s, d) => s + d.cachedRequests, 0),
    threats: daily.reduce((s, d) => s + d.threats, 0),
    uniques: daily.reduce((s, d) => s + d.uniques, 0),
    bytes: daily.reduce((s, d) => s + d.bytes, 0),
  };
  totals.cacheRatio = totals.requests ? (totals.cachedRequests / totals.requests * 100).toFixed(1) : 0;

  const topCountries = Object.entries(countryAgg).sort((a,b) => b[1] - a[1]).slice(0, 15).map(([country, requests]) => ({ country, requests }));
  const statusCodes = Object.entries(statusAgg).sort((a,b) => b[1] - a[1]).map(([code, requests]) => ({ code: parseInt(code), requests }));

  return jsonResponse({
    zones: ALL_ZONES.map(z => z.name),
    days,
    since: sinceStr,
    until: untilStr,
    totals,
    perZone,
    daily,
    topCountries,
    statusCodes,
  });
}

// ═══════════════════════════════════════════════════════════════════════
// Cloudflare-powered dashboard — uses CF GraphQL Analytics API
// ═══════════════════════════════════════════════════════════════════════
function handleCloudflareDashboard(host) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cloudflare Analytics — ${host}</title>
<meta name="robots" content="noindex,nofollow">
<style>
:root {
  --bg: #0d1117; --card: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e; --accent: #f6821f;
  --green: #3fb950; --red: #f85149; --yellow: #d29922; --blue: #58a6ff;
  --purple: #bc8cff; --teal: #39c5cf;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 1rem; max-width: 1400px; margin: 0 auto; }
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; margin: 1.5rem 0 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.grid { display: grid; gap: 0.75rem; }
.grid-6 { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
.grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
.stat { text-align: center; }
.stat .num { font-size: 1.8rem; font-weight: 700; }
.stat .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }
.stat.accent .num { color: var(--accent); }
.stat.green .num { color: var(--green); }
.stat.red .num { color: var(--red); }
.stat.blue .num { color: var(--blue); }
.stat.purple .num { color: var(--purple); }
.stat.teal .num { color: var(--teal); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
tr:hover { background: rgba(246,130,31,0.05); }
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
.badge.green { background: rgba(63,185,80,0.2); color: var(--green); }
.badge.red { background: rgba(248,81,73,0.2); color: var(--red); }
.badge.yellow { background: rgba(210,153,34,0.2); color: var(--yellow); }
.badge.blue { background: rgba(88,166,255,0.2); color: var(--blue); }
.badge.orange { background: rgba(246,130,31,0.2); color: var(--accent); }
.bar-chart { display: flex; align-items: flex-end; gap: 4px; height: 120px; margin-top: 0.5rem; }
.bar { flex: 1; border-radius: 3px 3px 0 0; min-height: 2px; position: relative; transition: height 0.3s; cursor: pointer; }
.bar.cached { background: var(--green); }
.bar.uncached { background: var(--accent); }
.bar:hover { opacity: 0.8; }
.bar-label { position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); font-size: 0.6rem; color: var(--muted); }
.bar-container { padding-bottom: 1.5rem; }
.empty { color: var(--muted); font-style: italic; padding: 1rem 0; }
.refresh { position: fixed; top: 1rem; right: 1rem; background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; z-index: 100; }
.refresh:hover { border-color: var(--accent); }
.loading { opacity: 0.5; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.geo-row { display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }
.geo-bar { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.geo-fill { height: 100%; border-radius: 4px; }
.legend { display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; color: var(--muted); }
.legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.error-banner { background: rgba(248,81,73,0.1); border: 1px solid var(--red); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; color: var(--red); font-size: 0.85rem; }
.back-link { margin-bottom: 1rem; font-size: 0.85rem; }
@media(max-width:768px) { .grid-3, .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<button class="refresh" onclick="loadData()">↻ Refresh</button>
<h1>Cloudflare Analytics Dashboard</h1>
<p class="subtitle">${host} — infrastructure-level metrics from Cloudflare's GraphQL Analytics API</p>
<div class="back-link"><a href="/dashboard">← Back to MO§ES Analytics</a></div>

<div id="error-banner" style="display:none"></div>

<h2>Overview (Last 7 Days — All Zones)</h2>
<div class="grid grid-6" id="overview">
  <div class="card stat accent"><div class="num" id="ov-requests">-</div><div class="label">Total Requests</div></div>
  <div class="card stat blue"><div class="num" id="ov-pageviews">-</div><div class="label">Page Views</div></div>
  <div class="card stat green"><div class="num" id="ov-cache">-</div><div class="label">Cache Hit %</div></div>
  <div class="card stat purple"><div class="num" id="ov-uniques">-</div><div class="label">Unique Visitors</div></div>
  <div class="card stat teal"><div class="num" id="ov-bandwidth">-</div><div class="label">Bandwidth</div></div>
  <div class="card stat red"><div class="num" id="ov-threats">-</div><div class="label">Threats</div></div>
</div>

<h2>Per-Zone Breakdown</h2>
<div class="card" style="overflow-x:auto">
  <table>
    <thead><tr><th>Zone</th><th>Requests</th><th>Page Views</th><th>Cache %</th><th>Uniques</th><th>Threats</th><th>Bandwidth</th></tr></thead>
    <tbody id="perzone-table"><tr><td colspan="7" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>Daily Traffic (All Zones — Requests & Cache Ratio)</h2>
<div class="card bar-container">
  <div class="bar-chart" id="bar-chart"></div>
  <div class="legend">
    <span><span class="legend-dot" style="background:var(--green)"></span>Cached</span>
    <span><span class="legend-dot" style="background:var(--accent)"></span>Uncached</span>
  </div>
</div>

<h2>Top Countries</h2>
<div class="grid grid-2">
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By Request Volume</h3>
    <div id="countries"><div class="empty">Loading...</div></div>
  </div>
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">Daily Breakdown</h3>
    <div id="countries-daily"><div class="empty">Loading...</div></div>
  </div>
</div>

<h2>HTTP Status Codes</h2>
<div class="card" id="status-card">
  <table>
    <thead><tr><th>Status</th><th>Description</th><th>Requests</th><th>% of Total</th></tr></thead>
    <tbody id="status-table"><tr><td colspan="4" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>Daily Detail</h2>
<div class="card" style="overflow-x:auto">
  <table>
    <thead><tr><th>Date</th><th>Requests</th><th>Page Views</th><th>Cached</th><th>Cache %</th><th>Uniques</th><th>Threats</th><th>Bandwidth</th></tr></thead>
    <tbody id="daily-table"><tr><td colspan="8" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<script>
function formatBytes(b) {
  if (!b) return '0 B';
  const units = ['B','KB','MB','GB','TB'];
  const i = Math.floor(Math.log(b) / Math.log(1024));
  return (b / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
}

function statusName(code) {
  const names = {200:'OK',201:'Created',204:'No Content',301:'Moved Permanently',302:'Found',304:'Not Modified',307:'Temporary Redirect',308:'Permanent Redirect',400:'Bad Request',401:'Unauthorized',403:'Forbidden',404:'Not Found',405:'Method Not Allowed',429:'Too Many Requests',500:'Internal Server Error',502:'Bad Gateway',503:'Service Unavailable',504:'Gateway Timeout',521:'Web Server Down',522:'Connection Timed Out',523:'Origin Unreachable',530:'Origin DNS Error'};
  return names[code] || '';
}

function statusBadge(code) {
  if (code >= 200 && code < 300) return 'green';
  if (code >= 300 && code < 400) return 'blue';
  if (code >= 400 && code < 500) return 'yellow';
  if (code >= 500) return 'red';
  return '';
}

async function loadData() {
  document.body.classList.add('loading');
  const d = await fetch('/api/analytics/cloudflare?days=7').then(r => r.json()).catch(() => null);
  document.body.classList.remove('loading');

  if (!d || d.error) {
    const banner = document.getElementById('error-banner');
    banner.style.display = '';
    banner.innerHTML = '<strong>Setup required:</strong> ' + (d?.error || d?.hint || 'Failed to load Cloudflare analytics') + '<br><br>Run: <code>wrangler secret put CF_API_TOKEN</code> in the analytics-worker directory. Create a token at <a href="https://dash.cloudflare.com/profile/api-tokens" target="_blank">Cloudflare API Tokens</a> with "Zone Analytics Read" for mos2es.org.';
    return;
  }

  // Overview
  const t = d.totals;
  document.getElementById('ov-requests').textContent = t.requests.toLocaleString();
  document.getElementById('ov-pageviews').textContent = t.pageViews.toLocaleString();
  document.getElementById('ov-cache').textContent = t.cacheRatio + '%';
  document.getElementById('ov-uniques').textContent = t.uniques.toLocaleString();
  document.getElementById('ov-bandwidth').textContent = formatBytes(t.bytes);
  document.getElementById('ov-threats').textContent = t.threats.toLocaleString();

  // Per-zone breakdown
  const perZone = d.perZone || [];
  document.getElementById('perzone-table').innerHTML = perZone.length
    ? perZone.map(z => '<tr><td><strong>' + z.zone + '</strong>' + (z.error ? ' <span class="badge red">error</span>' : '') + '</td><td>' + z.requests.toLocaleString() + '</td><td>' + z.pageViews.toLocaleString() + '</td><td>' + z.cacheRatio + '%</td><td>' + z.uniques.toLocaleString() + '</td><td>' + z.threats + '</td><td>' + formatBytes(z.bytes) + '</td></tr>').join('')
    : '<tr><td colspan="7" class="empty">No zone data</td></tr>';

  // Bar chart - stacked cached/uncached
  const daily = d.daily || [];
  const maxReq = Math.max(...daily.map(d => d.requests), 1);
  document.getElementById('bar-chart').innerHTML = daily.map(d => {
    const cachedH = (d.cachedRequests / maxReq) * 110;
    const uncachedH = ((d.requests - d.cachedRequests) / maxReq) * 110;
    const label = d.date.slice(5);
    return '<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center">' +
      '<div class="bar uncached" style="height:' + uncachedH + 'px;width:70%" title="Uncached: ' + (d.requests - d.cachedRequests) + '"></div>' +
      '<div class="bar cached" style="height:' + cachedH + 'px;width:70%" title="Cached: ' + d.cachedRequests + ' (' + d.cacheRatio + '%)"></div>' +
      '<span class="bar-label">' + label + '</span></div>';
  }).join('');

  // Top countries
  const countries = d.topCountries || [];
  const maxCountry = countries[0]?.requests || 1;
  document.getElementById('countries').innerHTML = countries.length
    ? countries.map(c => '<div class="geo-row"><span style="min-width:50px;font-size:0.8rem">' + c.country + '</span><div class="geo-bar"><div class="geo-fill" style="width:' + (c.requests/maxCountry*100) + '%;background:var(--accent)"></div></div><span style="min-width:60px;text-align:right;font-size:0.8rem">' + c.requests.toLocaleString() + '</span></div>').join('')
    : '<div class="empty">No country data</div>';

  // Countries daily (top 5 countries by day)
  const top5 = countries.slice(0, 5).map(c => c.country);
  if (top5.length) {
    document.getElementById('countries-daily').innerHTML = '<table><thead><tr><th>Date</th>' + top5.map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>' +
      daily.map(d => {
        const dayCountries = {};
        for (const c of d.countries) dayCountries[c.clientCountryName] = c.requests;
        return '<tr><td>' + d.date.slice(5) + '</td>' + top5.map(c => '<td>' + (dayCountries[c] || 0) + '</td>').join('') + '</tr>';
      }).join('') + '</tbody></table>';
  } else {
    document.getElementById('countries-daily').innerHTML = '<div class="empty">No data</div>';
  }

  // Status codes
  const statuses = d.statusCodes || [];
  const totalReqs = t.requests || 1;
  document.getElementById('status-table').innerHTML = statuses.length
    ? statuses.map(s => '<tr><td><span class="badge ' + statusBadge(s.code) + '">' + s.code + '</span></td><td>' + statusName(s.code) + '</td><td>' + s.requests.toLocaleString() + '</td><td>' + (s.requests/totalReqs*100).toFixed(1) + '%</td></tr>').join('')
    : '<tr><td colspan="4" class="empty">No status code data</td></tr>';

  // Daily table
  document.getElementById('daily-table').innerHTML = daily.length
    ? daily.map(d => '<tr><td>' + d.date + '</td><td>' + d.requests.toLocaleString() + '</td><td>' + d.pageViews.toLocaleString() + '</td><td>' + d.cachedRequests.toLocaleString() + '</td><td>' + d.cacheRatio + '%</td><td>' + d.uniques.toLocaleString() + '</td><td>' + d.threats + '</td><td>' + formatBytes(d.bytes) + '</td></tr>').join('')
    : '<tr><td colspan="8" class="empty">No daily data</td></tr>';
}

loadData();
setInterval(loadData, 300000); // 5 min refresh
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
  --orange: #db6d28; --teal: #39c5cf;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 1rem; max-width: 1400px; margin: 0 auto; }
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; margin: 1.5rem 0 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.grid { display: grid; gap: 0.75rem; }
.grid-6 { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
.grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
.stat { text-align: center; }
.stat .num { font-size: 1.8rem; font-weight: 700; }
.stat .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }
.stat.human .num { color: var(--green); }
.stat.bot .num { color: var(--yellow); }
.stat.total .num { color: var(--accent); }
.stat.ai .num { color: var(--purple); }
.stat.ratio .num { color: var(--orange); }
.stat.unique .num { color: var(--teal); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
tr:hover { background: rgba(88,166,255,0.05); }
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
.badge.green { background: rgba(63,185,80,0.2); color: var(--green); }
.badge.yellow { background: rgba(210,153,34,0.2); color: var(--yellow); }
.badge.blue { background: rgba(88,166,255,0.2); color: var(--accent); }
.badge.purple { background: rgba(188,140,255,0.2); color: var(--purple); }
.badge.red { background: rgba(248,81,73,0.2); color: var(--red); }
.badge.orange { background: rgba(219,109,40,0.2); color: var(--orange); }
.badge.teal { background: rgba(57,197,207,0.2); color: var(--teal); }
.bar-chart { display: flex; align-items: flex-end; gap: 4px; height: 100px; margin-top: 0.5rem; }
.bar { flex: 1; border-radius: 3px 3px 0 0; min-height: 2px; position: relative; transition: height 0.3s; cursor: pointer; }
.bar.human { background: var(--green); }
.bar.bot { background: var(--yellow); }
.bar:hover { opacity: 0.8; }
.bar-label { position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); font-size: 0.6rem; color: var(--muted); }
.bar-container { padding-bottom: 1.5rem; }
.empty { color: var(--muted); font-style: italic; padding: 1rem 0; }
.refresh { position: fixed; top: 1rem; right: 1rem; background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; z-index: 100; }
.refresh:hover { border-color: var(--accent); }
.loading { opacity: 0.5; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.endpoints { font-size: 0.75rem; }
.endpoints code { background: var(--bg); padding: 0.2rem 0.4rem; border-radius: 3px; color: var(--green); }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.tab { padding: 0.4rem 0.8rem; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 0.8rem; color: var(--muted); }
.tab.active { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.ratio-bar { display: flex; height: 24px; border-radius: 4px; overflow: hidden; margin-top: 0.3rem; }
.ratio-crawl { background: var(--yellow); }
.ratio-referral { background: var(--green); }
.ratio-label { font-size: 0.7rem; color: var(--muted); margin-top: 0.2rem; display: flex; justify-content: space-between; }
.geo-row { display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }
.geo-bar { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.geo-fill { height: 100%; background: var(--accent); border-radius: 4px; }
.mono { font-family: 'SF Mono', Monaco, monospace; font-size: 0.75rem; }
.progress-ring { width: 80px; height: 80px; position: relative; margin: 0 auto; }
.progress-ring svg { transform: rotate(-90deg); }
.progress-ring circle { fill: none; stroke-width: 6; }
.progress-ring .bg { stroke: var(--border); }
.progress-ring .fg { stroke: var(--accent); transition: stroke-dashoffset 0.5s; }
.progress-ring .text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 1.2rem; font-weight: 700; }
@media(max-width:768px) { .grid-3, .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<button class="refresh" onclick="loadAll()">↻ Refresh</button>
<h1>MO\u00a7ES\u2122 Analytics Dashboard</h1>
<p class="subtitle">${host} \u2014 agent intelligence, crawl economics & visitor monitoring</p>

<div class="tabs">
  <div class="tab active" onclick="switchTab('overview')">Overview</div>
  <div class="tab" onclick="switchTab('agents')">Agent Trail</div>
  <div class="tab" onclick="switchTab('economics')">Crawl Economics</div>
  <div class="tab" onclick="switchTab('geo')">Geographic</div>
</div>

<!-- ═══ OVERVIEW TAB ═══ -->
<div id="tab-overview">
<h2>Realtime</h2>
<div class="grid grid-6" id="realtime">
  <div class="card stat total"><div class="num" id="rt-total">-</div><div class="label">Today Total</div></div>
  <div class="card stat human"><div class="num" id="rt-human">-</div><div class="label">Human Today</div></div>
  <div class="card stat bot"><div class="num" id="rt-bots">-</div><div class="label">Bots Today</div></div>
  <div class="card stat total"><div class="num" id="rt-all">-</div><div class="label">All Time</div></div>
  <div class="card stat ai"><div class="num" id="rt-engines">-</div><div class="label">AI Engines</div></div>
  <div class="card stat unique"><div class="num" id="rt-unique">-</div><div class="label">Unique IPs</div></div>
</div>

<h2>7-Day Activity</h2>
<div class="card bar-container">
  <div class="bar-chart" id="bar-chart"></div>
</div>

<h2>Agent Readiness Score</h2>
<div class="grid grid-2">
  <div class="card" style="text-align:center">
    <div class="progress-ring" id="readiness-ring">
      <svg width="80" height="80"><circle class="bg" cx="40" cy="40" r="35"/><circle class="fg" cx="40" cy="40" r="35" stroke-dasharray="220" stroke-dashoffset="220" id="ring-fg"/></svg>
      <div class="text" id="ring-text">0%</div>
    </div>
    <p style="margin-top:0.5rem;color:var(--muted);font-size:0.85rem" id="readiness-detail">Loading...</p>
  </div>
  <div class="card" id="readiness-engines">
    <div class="empty">Loading...</div>
  </div>
</div>

<h2>AI Crawler Presence</h2>
<div class="card" id="bots-card">
  <table>
    <thead><tr><th>Engine</th><th>Bot</th><th>Type</th><th>Visits</th><th>Last Seen</th></tr></thead>
    <tbody id="bots-table"><tr><td colspan="5" class="empty">Loading...</td></tr></tbody>
  </table>
</div>

<h2>By Type</h2>
<div class="card" id="types-card">
  <table>
    <thead><tr><th>Event Type</th><th>Count</th></tr></thead>
    <tbody id="types-table"><tr><td colspan="2" class="empty">Loading...</td></tr></tbody>
  </table>
</div>
</div>

<!-- ═══ AGENT TRAIL TAB ═══ -->
<div id="tab-agents" style="display:none">
<h2>Agent Provenance — Where Are They Coming From?</h2>
<div class="grid grid-3">
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By Country</h3>
    <div id="trail-country"><div class="empty">Loading...</div></div>
  </div>
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By Network (ASN)</h3>
    <div id="trail-asn"><div class="empty">Loading...</div></div>
  </div>
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By Content Type</h3>
    <div id="trail-accept"><div class="empty">Loading...</div></div>
  </div>
</div>

<h2>By City</h2>
<div class="card" id="trail-city-card">
  <div id="trail-city"><div class="empty">Loading...</div></div>
</div>

<h2>By Referrer</h2>
<div class="card" id="trail-referrer-card">
  <div id="trail-referrer"><div class="empty">Loading...</div></div>
</div>

<h2>Recent Agent Visits (Last 50)</h2>
<div class="card" style="overflow-x:auto">
  <table>
    <thead><tr><th>Bot</th><th>Engine</th><th>Type</th><th>Path</th><th>Country</th><th>City</th><th>ASN</th><th>Referrer</th><th>Accept</th><th>When</th></tr></thead>
    <tbody id="trail-table"><tr><td colspan="10" class="empty">Loading...</td></tr></tbody>
  </table>
</div>
</div>

<!-- ═══ CRAWL ECONOMICS TAB ═══ -->
<div id="tab-economics" style="display:none">
<h2>Crawl-to-Referral Ratio</h2>
<p class="subtitle" style="margin-bottom:0.75rem">How many times each AI engine crawls your site vs how much traffic they send back. Per Cloudflare's Agentic Internet Bot Report.</p>

<div class="grid grid-4" id="economics-summary">
  <div class="card stat total"><div class="num" id="eco-total-crawls">-</div><div class="label">Total Crawls</div></div>
  <div class="card stat human"><div class="num" id="eco-total-referrals">-</div><div class="label">Total Referrals</div></div>
  <div class="card stat ratio"><div class="num" id="eco-ratio">-</div><div class="label">Overall Ratio</div></div>
  <div class="card stat ai"><div class="num" id="eco-engines">-</div><div class="label">Engines Active</div></div>
</div>

<h2>Per-Engine Breakdown</h2>
<div class="card" id="economics-engines-card">
  <div id="economics-engines"><div class="empty">Loading...</div></div>
</div>

<h2>7-Day Trend</h2>
<div class="card" id="economics-trend-card">
  <div id="economics-trend"><div class="empty">Loading...</div></div>
</div>
</div>

<!-- ═══ GEOGRAPHIC TAB ═══ -->
<div id="tab-geo" style="display:none">
<h2>Geographic Distribution</h2>
<div class="grid grid-2">
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By Country</h3>
    <div id="geo-country"><div class="empty">Loading...</div></div>
  </div>
  <div class="card">
    <h3 style="font-size:0.85rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.5rem">By City</h3>
    <div id="geo-city"><div class="empty">Loading...</div></div>
  </div>
</div>

<h2>By Path (Most Crawled)</h2>
<div class="card" id="geo-path-card">
  <div id="geo-path"><div class="empty">Loading...</div></div>
</div>
</div>

<!-- ═══ API ENDPOINTS ═══ -->
<h2>API Endpoints</h2>
<div class="card endpoints">
  <code>GET /api/analytics/realtime</code> — current counters<br>
  <code>GET /api/analytics/stats?days=7</code> — aggregated stats<br>
  <code>GET /api/analytics/bots</code> — AI crawler visits<br>
  <code>GET /api/analytics/agent-trail</code> — agent provenance<br>
  <code>GET /api/analytics/crawl-referral-ratio</code> — crawl economics<br>
  <code>GET /api/analytics/ai-overview</code> — AI engine visibility<br>
  <code>GET /api/analytics/web-vitals</code> — Core Web Vitals<br>
  <code>POST /api/analytics/beacon</code> — record event<br>
  <code>GET /.well-known/agent.json</code> — agent manifest<br>
  <code>GET /crawl-control.json</code> — crawl rules<br>
  <code>GET /dashboard</code> — this page
</div>

<script>
let currentTab = 'overview';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tab).style.display = '';
  event.target.classList.add('active');
  loadTabData(tab);
}

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

function truncate(str, n) { return str ? (str.length > n ? str.slice(0,n) + '…' : str) : '-'; }

function makeGeoBars(data, color) {
  const entries = Object.entries(data).sort((a,b) => b[1]-a[1]).slice(0, 15);
  if (!entries.length) return '<div class="empty">No data yet</div>';
  const max = entries[0][1];
  return entries.map(([k,v]) => 
    '<div class="geo-row"><span style="min-width:80px;font-size:0.8rem">' + truncate(k, 12) + '</span>' +
    '<div class="geo-bar"><div class="geo-fill" style="width:' + (v/max*100) + '%;background:' + color + '"></div></div>' +
    '<span style="min-width:40px;text-align:right;font-size:0.8rem">' + v + '</span></div>'
  ).join('');
}

// ─── Realtime ─────────────────────────────────────────
async function loadRealtime() {
  const d = await fetchJSON('/api/analytics/realtime');
  if (!d || !d.realtime) return;
  const r = d.realtime;
  document.getElementById('rt-total').textContent = r.todayTotal;
  document.getElementById('rt-human').textContent = r.todayHuman;
  document.getElementById('rt-bots').textContent = r.todayBots;
  document.getElementById('rt-all').textContent = r.totalAllTime;
}

// ─── Stats + 7-day chart ──────────────────────────────
async function loadStats() {
  const d = await fetchJSON('/api/analytics/stats?days=7');
  if (!d || !d.byDay) return;
  const days = Object.entries(d.byDay).sort();
  const max = Math.max(...days.map(([,v]) => v.total), 1);
  const chart = document.getElementById('bar-chart');
  chart.innerHTML = days.map(([date, v]) => {
    const humanH = (v.human / max) * 90;
    const botH = (v.bots / max) * 90;
    const label = date.slice(5);
    return '<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center">' +
      '<div class="bar bot" style="height:' + botH + 'px;width:60%" title="Bots: ' + v.bots + '"></div>' +
      '<div class="bar human" style="height:' + humanH + 'px;width:60%" title="Human: ' + v.human + '"></div>' +
      '<span class="bar-label">' + label + '</span></div>';
  }).join('');

  if (d.byType) {
    const types = Object.entries(d.byType).sort((a,b) => b[1] - a[1]);
    document.getElementById('types-table').innerHTML = types.length
      ? types.map(([t,c]) => '<tr><td><span class="badge blue">' + t + '</span></td><td>' + c + '</td></tr>').join('')
      : '<tr><td colspan="2" class="empty">No events yet</td></tr>';
  }
}

// ─── Bots ─────────────────────────────────────────────
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

// ─── AI Overview + Readiness ──────────────────────────
async function loadAiOverview() {
  const d = await fetchJSON('/api/analytics/ai-overview');
  if (!d) return;
  const score = d.readinessScore || 0;
  const total = d.totalKnownEngines || 18;
  const pct = Math.round((score / total) * 100);
  
  // Progress ring
  const circumference = 220;
  const offset = circumference - (pct / 100) * circumference;
  document.getElementById('ring-fg').setAttribute('stroke-dashoffset', offset);
  document.getElementById('ring-text').textContent = pct + '%';
  document.getElementById('readiness-detail').textContent = score + ' of ' + total + ' AI engines have crawled this site';
  
  const presence = d.crawlerPresence || {};
  const engines = Object.entries(presence).map(([engine, info]) =>
    '<span class="badge ' + (info.type === 'training' ? 'yellow' : 'blue') + '" style="margin:0.2rem">' + engine + ' (' + info.visits + ')</span>'
  ).join(' ');
  document.getElementById('readiness-engines').innerHTML = engines || '<div class="empty">No AI engines have crawled this site yet</div>';
  document.getElementById('rt-engines').textContent = score;
}

// ─── Agent Trail ──────────────────────────────────────
async function loadAgentTrail() {
  const d = await fetchJSON('/api/analytics/agent-trail?limit=50');
  if (!d) return;
  
  const prov = d.provenance || {};
  document.getElementById('trail-country').innerHTML = makeGeoBars(prov.byCountry || {}, 'var(--accent)');
  document.getElementById('trail-asn').innerHTML = makeGeoBars(prov.byAsn || {}, 'var(--purple)');
  document.getElementById('trail-accept').innerHTML = makeGeoBars(prov.byAcceptType || {}, 'var(--teal)');
  document.getElementById('trail-city').innerHTML = makeGeoBars(prov.byCity || {}, 'var(--green)');
  document.getElementById('trail-referrer').innerHTML = makeGeoBars(prov.byReferrer || {}, 'var(--orange)');
  document.getElementById('geo-country').innerHTML = makeGeoBars(prov.byCountry || {}, 'var(--accent)');
  document.getElementById('geo-city').innerHTML = makeGeoBars(prov.byCity || {}, 'var(--green)');
  document.getElementById('geo-path').innerHTML = makeGeoBars(prov.byPath || {}, 'var(--purple)');
  
  document.getElementById('rt-unique').textContent = d.uniqueVisitors || 0;
  
  const trail = d.trail || [];
  document.getElementById('trail-table').innerHTML = trail.length
    ? trail.map(e => '<tr><td>' + (e.bot || '-') + '</td><td><strong>' + (e.engine || '-') + '</strong></td><td><span class="badge ' + (e.type === 'training' ? 'yellow' : e.type === 'unknown' ? 'red' : 'blue') + '">' + (e.type || '-') + '</span></td><td class="mono">' + truncate(e.path, 30) + '</td><td>' + (e.country || '-') + '</td><td>' + truncate(e.city || '-', 10) + '</td><td class="mono">' + (e.asn ? 'AS' + e.asn : '-') + '</td><td class="mono">' + truncate(e.referrer || '', 20) + '</td><td class="mono">' + truncate(e.acceptHeader || '-', 15) + '</td><td>' + timeAgo(e.timestamp) + '</td></tr>').join('')
    : '<tr><td colspan="10" class="empty">No agent visits recorded yet</td></tr>';
}

// ─── Crawl-Referral Ratio ─────────────────────────────
async function loadCrawlReferralRatio() {
  const d = await fetchJSON('/api/analytics/crawl-referral-ratio?days=7');
  if (!d) return;
  const s = d.summary || {};
  
  document.getElementById('eco-total-crawls').textContent = s.totalCrawls || 0;
  document.getElementById('eco-total-referrals').textContent = s.totalReferrals || 0;
  document.getElementById('eco-ratio').textContent = s.overallRatioLabel || '\u221e';
  document.getElementById('eco-engines').textContent = s.enginesTracked || 0;
  
  const engines = d.engines || [];
  if (!engines.length) {
    document.getElementById('economics-engines').innerHTML = '<div class="empty">No crawl or referral data yet. Data populates as bots crawl and humans arrive via AI referrers.</div>';
    document.getElementById('economics-trend').innerHTML = '<div class="empty">No trend data yet.</div>';
    return;
  }
  
  // Per-engine breakdown
  document.getElementById('economics-engines').innerHTML = 
    '<table><thead><tr><th>Engine</th><th>Crawls</th><th>Referrals</th><th>Ratio</th><th>Distribution</th></tr></thead><tbody>' +
    engines.map(e => {
      const total = e.allTime.crawls + e.allTime.referrals || 1;
      const crawlPct = (e.allTime.crawls / total * 100).toFixed(0);
      const referralPct = (e.allTime.referrals / total * 100).toFixed(0);
      return '<tr><td><strong>' + e.engine + '</strong></td><td>' + e.allTime.crawls + '</td><td>' + e.allTime.referrals + '</td><td><span class="badge ' + (e.allTime.ratio > 100 ? 'red' : e.allTime.ratio > 10 ? 'orange' : 'green') + '">' + e.allTime.ratioLabel + ':1</span></td><td style="min-width:150px"><div class="ratio-bar"><div class="ratio-crawl" style="width:' + crawlPct + '%"></div><div class="ratio-referral" style="width:' + referralPct + '%"></div></div><div class="ratio-label"><span>' + crawlPct + '% crawl</span><span>' + referralPct + '% referral</span></div></td></tr>';
    }).join('') + '</tbody></table>';
  
  // 7-day trend
  const allDays = new Set();
  engines.forEach(e => Object.keys(e.byDay).forEach(d => allDays.add(d)));
  const sortedDays = [...allDays].sort();
  if (sortedDays.length) {
    document.getElementById('economics-trend').innerHTML = 
      '<table><thead><tr><th>Date</th>' + engines.slice(0, 5).map(e => '<th>' + truncate(e.engine, 12) + '</th>').join('') + '</tr></thead><tbody>' +
      sortedDays.map(d => '<tr><td>' + d.slice(5) + '</td>' + engines.slice(0, 5).map(e => {
        const day = e.byDay[d];
        if (!day) return '<td>-</td>';
        return '<td>' + day.crawls + 'C / ' + day.referrals + 'R</td>';
      }).join('') + '</tr>').join('') + '</tbody></table>';
  } else {
    document.getElementById('economics-trend').innerHTML = '<div class="empty">No daily breakdown yet.</div>';
  }
}

// ─── Tab loader ───────────────────────────────────────
function loadTabData(tab) {
  if (tab === 'agents') loadAgentTrail();
  if (tab === 'economics') loadCrawlReferralRatio();
  if (tab === 'geo') loadAgentTrail();
}

async function loadAll() {
  document.body.classList.add('loading');
  await Promise.all([loadRealtime(), loadStats(), loadBots(), loadAiOverview(), loadAgentTrail(), loadCrawlReferralRatio()]);
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
