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
        { url: '/killer-experiment', title: 'Killer Experiment', keywords: ['killer', 'experiment', '15k', '30 days'] },
        { url: '/commercial-offer', title: 'Commercial Offer', keywords: ['commercial', 'pricing', 'offer', 'pilot', 'annual'] }
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
    description: 'Get a MOSES canonical metric definition. Available metrics: yield, leverage, token-snr, construction, divergence.',
    inputSchema: {
      type: 'object',
      properties: {
        metric: {
          type: 'string',
          enum: ['yield', 'leverage', 'token-snr', 'construction', 'divergence'],
          description: 'The metric to retrieve'
        }
      },
      required: ['metric']
    },
    annotations: { readOnlyHint: true },
    async execute({ metric }) {
      const metrics = {
        'yield': 'Yield (U): (cache_read x output) / input^2. Measures how efficiently an operator converts input tokens into useful output, boosted by cache reuse. The canonical efficiency metric in the Upsilon measurement engine.',
        'leverage': 'Leverage: output / input. Measures the raw amplification of an operator\'s input tokens into output. Higher leverage means more output per token of input.',
        'token-snr': 'Token SNR (Signal-to-Noise Ratio): The ratio of productive tokens to total tokens. Measures how much of the token budget is actually useful work versus noise.',
        'construction': 'Construction: Measures how much of the output is genuinely new construction versus regurgitation or minor edits. Higher construction means more original work.',
        'divergence': 'Divergence: Measures the semantic distance between an operator\'s output and reference outputs. Higher divergence can indicate either creativity or drift.'
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
          enum: ['home', 'product', 'pilot', 'methodology', 'research', 'demo', 'docs', 'about', 'contact', 'faq', 'killer-experiment', 'commercial-offer'],
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
        'killer-experiment': '/killer-experiment',
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
      return { content: [{ type: 'text', text: 'MOSES Enterprise Commercial Offers:\n\n1. Killer Experiment: $15K, 30 days\n   - Prove or disprove that AI operator evaluation reveals actionable gaps\n   - 10-operator evaluation with full metrics\n   - See: https://mos2es.org/killer-experiment\n\n2. Upsilon Pilot: $45K, 90 days\n   - Full enterprise pilot with the Upsilon measurement engine\n   - 50-operator evaluation, benchmarking, diagnosis, intervention\n   - See: https://mos2es.org/pilot\n\n3. Annual Operating Index: $150K/year\n   - Continuous evaluation and benchmarking\n   - Quarterly readouts and trend analysis\n   - See: https://mos2es.org/commercial-offer\n\nContact: pilots@mos2es.org' }] };
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
