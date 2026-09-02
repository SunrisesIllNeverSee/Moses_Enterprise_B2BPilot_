// WebMCP: Register browser-native tools for AI agents
// Spec: https://developer.chrome.com/docs/ai/webmcp/imperative-api
// Feature-detect both document.modelContext and navigator.modelContext

(function () {
  'use strict';

  const mc =
    (typeof document !== 'undefined' && document.modelContext) ||
    (typeof navigator !== 'undefined' && navigator.modelContext);

  if (!mc || typeof mc.registerTool !== 'function') {
    return;
  }

  // Tool: Search MOSES Enterprise content
  mc.registerTool({
    name: 'search_moses_enterprise',
    description: 'Search the MOSES Enterprise site for methodology, pilots, research, or commercial offerings. Returns relevant page URLs and titles.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query for MOSES Enterprise content'
        }
      },
      required: ['query']
    },
    annotations: { readOnlyHint: true },
    async execute({ query }) {
      const q = String(query || '').toLowerCase();
      const pages = [
        { url: '/product', title: 'Product', keywords: ['product', 'platform', 'features', 'upsilon'] },
        { url: '/pilot', title: 'Pilot', keywords: ['pilot', 'enterprise', 'trial', 'upsilon pilot'] },
        { url: '/methodology', title: 'Methodology', keywords: ['methodology', 'metrics', 'yield', 'leverage', 'token snr', 'construction', 'divergence'] },
        { url: '/research', title: 'Research', keywords: ['research', 'benchmark', 'reference', 'population', 'evidence'] },
        { url: '/demo', title: 'Demo', keywords: ['demo', 'walkthrough', 'interactive', 'evaluate', 'diagnose'] },
        { url: '/docs', title: 'Documentation', keywords: ['docs', 'documentation', 'api', 'mcp', 'cli'] },
        { url: '/about', title: 'About', keywords: ['about', 'company', 'ello cello', 'team'] },
        { url: '/contact', title: 'Contact', keywords: ['contact', 'demo', 'book', 'pilot', 'commercial'] },
        { url: '/faq', title: 'FAQ', keywords: ['faq', 'questions', 'answers', 'help'] },
        { url: '/baseline-assessment', title: 'Baseline Assessment', keywords: ['baseline', 'assessment', '15k', '30 days'] },
        { url: '/commercial-offer', title: 'Commercial Offer', keywords: ['commercial', 'offer', 'pilot', 'baseline'] }
      ];
      const matches = pages.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.keywords.some(k => k.includes(q) || q.includes(k))
      );
      if (matches.length === 0) {
        return { content: [{ type: 'text', text: 'No results found for: ' + query + '. Try: methodology, pilot, research, demo, pricing, contact.' }] };
      }
      const results = matches.map(p => '- [' + p.title + '](https://mos2es.org' + p.url + ')').join('\n');
      return { content: [{ type: 'text', text: 'Results for "' + query + '":\n' + results }] };
    }
  });

  // Tool: Get MOSES metric definition
  mc.registerTool({
    name: 'get_metric',
    description: 'Get a MOSES canon metric definition. Available metrics: yield, leverage, token-snr, 10xdev, construction, velocity, scale-v, efficiency.',
    inputSchema: {
      type: 'object',
      properties: {
        metric: {
          type: 'string',
          enum: ['yield', 'leverage', 'token-snr', '10xdev', 'construction', 'velocity', 'scale-v', 'efficiency'],
          description: 'The metric to retrieve'
        }
      },
      required: ['metric']
    },
    annotations: { readOnlyHint: true },
    async execute({ metric }) {
      const metrics = {
        'yield': 'Yield (Υ): (cache_read × output) / input². The signature Upsilon metric — how efficiently an operator converts input tokens into useful output, boosted by cache reuse. Cascade: Transmission × Commitment × Reuse.',
        'leverage': 'Leverage: cache_read / input. Cache reuse per fresh input. Higher leverage means more cache reads per token of fresh input.',
        'token-snr': 'Token SNR: output / (input + output). Output share of fresh flow. Measures how much of the token budget is actually useful output.',
        '10xdev': '10xDEV: log₁₀(leverage). Logarithmic cascade summary — the order-of-magnitude scale of cache reuse efficiency.',
        'construction': 'Construction: cache_write / cache_read. New context per read. Higher construction means more original context creation relative to reuse.',
        'velocity': 'Velocity: output / input. Output per fresh input. Measures raw output productivity per token of fresh input.',
        'scale-v': 'Scale V: log₁₀(input + output + cache_create + cache_read). Log token volume — the overall scale of processing activity.',
        'efficiency': 'Efficiency: (cache_read + cache_create + output) / input / 4. Display diagnostic only — composite flow efficiency.'
      };
      const result = metrics[metric] || 'Unknown metric: ' + metric;
      return { content: [{ type: 'text', text: result }] };
    }
  });

  // Tool: Navigate to a MOSES Enterprise page
  mc.registerTool({
    name: 'navigate_to',
    description: 'Navigate the browser to a MOSES Enterprise page. Use this when the user wants to view a specific page.',
    inputSchema: {
      type: 'object',
      properties: {
        page: {
          type: 'string',
          enum: ['home', 'product', 'pilot', 'methodology', 'research', 'demo', 'docs', 'about', 'contact', 'faq', 'baseline-assessment', 'commercial-offer'],
          description: 'The page to navigate to'
        }
      },
      required: ['page']
    },
    async execute({ page }) {
      const pages = {
        'home': '/',
        'product': '/product',
        'pilot': '/pilot',
        'methodology': '/methodology',
        'research': '/research',
        'demo': '/demo',
        'docs': '/docs',
        'about': '/about',
        'contact': '/contact',
        'faq': '/faq',
        'baseline-assessment': '/baseline-assessment',
        'commercial-offer': '/commercial-offer'
      };
      const path = pages[page] || '/';
      if (typeof window !== 'undefined') {
        window.location.href = path;
      }
      return { content: [{ type: 'text', text: 'Navigating to ' + page + ' (' + path + ')' }] };
    }
  });

  // Tool: Get pilot pricing
  mc.registerTool({
    name: 'get_pilot_pricing',
    description: 'Get MOSES Enterprise pilot pricing and commercial offerings.',
    inputSchema: {
      type: 'object',
      properties: {}
    },
    annotations: { readOnlyHint: true },
    async execute() {
      return { content: [{ type: 'text', text: 'MOSES Enterprise Commercial Offer:\n\n1. Baseline Assessment: $15K, 30 days\n   - Establish a measured baseline of your enterprise AI operating system\n   - 25-100 operator evaluation with full metrics\n   - Baseline, diagnose, intervene, re-measure, evidence report\n   - See: https://mos2es.org/commercial-offer\n\nExtended engagement available after the baseline. Contact to discuss.\n\nContact: pilots@mos2es.org' }] };
    }
  });

  // Tool: Get ecosystem info
  mc.registerTool({
    name: 'get_ecosystem',
    description: 'Get information about the MOSES ecosystem: architecture, related projects, and platforms.',
    inputSchema: {
      type: 'object',
      properties: {}
    },
    annotations: { readOnlyHint: true },
    async execute() {
      const ecosystem = [
        'MOSES: Governance framework and methodology',
        'Upsilon: Enterprise measurement engine (the engine that measures)',
        'SigRank: Public leaderboard and benchmark (signalaf.com)',
        'SignalAF: Public distribution and platform brand',
        'MCP Server (mcp.mos2es.org): 27 tools, 5 prompts, 6 resources',
        'Contribution Exchange: Agent contribution protocol via signalaf.com steward',
        'Architecture: MOSES -> Upsilon -> SigRank | SignalAF'
      ];
      return { content: [{ type: 'text', text: 'MOSES Ecosystem:\n' + ecosystem.join('\n') }] };
    }
  });
})();
