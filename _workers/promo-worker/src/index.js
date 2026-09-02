// MO§ES™ promo worker — static assets + AEO enhancements
// Handles: clean URLs, markdown content negotiation, JSON errors, Vary header
// Also: server-side bot detection for every request (beacon doesn't fire for crawlers)

import { WELL_KNOWN_INLINE } from './well-known-content.js';

// AI crawler detection — mirrors the analytics worker's list
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

function detectBot(userAgent) {
  if (!userAgent) return null;
  const ua = userAgent.toLowerCase();
  for (const [bot, info] of Object.entries(AI_CRAWLERS)) {
    if (ua.includes(bot)) return { bot, ...info };
  }
  if (ua.includes('bot') || ua.includes('crawler') || ua.includes('spider') || ua.includes('scraper')) {
    return { bot: 'generic', engine: 'Unknown', type: 'unknown' };
  }
  return null;
}

// Fire-and-forget beacon to the analytics worker
// Uses the analytics worker's URL, not internal fetch, so it works across workers
const ANALYTICS_BEACON_URL = 'https://moses-analytics.sigrank.workers.dev/api/analytics/beacon';

async function fireBeacon(request, host, path, botInfo) {
  try {
    const cf = request.cf || {};
    const referrer = request.headers.get('Referer') || null;
    const accept = request.headers.get('Accept') || '';
    await fetch(ANALYTICS_BEACON_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: botInfo ? 'crawl' : 'pageview',
        path: path,
        site: host,
        referrer: referrer,
        // Bot provenance — captured server-side, not from JS beacon
        bot: botInfo?.bot,
        engine: botInfo?.engine,
        botType: botInfo?.type,
        country: cf.country,
        region: cf.region,
        city: cf.city,
        colo: cf.colo,
        asn: cf.asn,
        asOrganization: cf.asOrganization,
        acceptHeader: accept,
        userAgent: request.headers.get('User-Agent') || '',
      }),
    });
  } catch (e) {
    // Fire-and-forget — don't let beacon failures affect the response
  }
}

// All pages that should be available as markdown via content negotiation
const MARKDOWN_PAGES = {
  '/': 'index',
  '/product': 'product',
  '/pilot': 'pilot',
  '/methodology': 'methodology',
  '/research': 'research',
  '/contact': 'contact',
  '/about': 'about',
  '/privacy': 'privacy',
  '/docs': 'docs',
  '/demo': 'demo',
  '/pilot-readout': 'pilot-readout',
  '/faq': 'faq',
  '/commercial-offer': 'commercial-offer',
  '/baseline-assessment': 'baseline-assessment',
};

// Simple HTML-to-Markdown converter for agent content negotiation
function htmlToMarkdown(html, path) {
  let md = html;
  // Remove script and style blocks entirely
  md = md.replace(/<script[\s\S]*?<\/script>/gi, '');
  md = md.replace(/<style[\s\S]*?<\/style>/gi, '');
  md = md.replace(/<nav[\s\S]*?<\/nav>/gi, '');
  md = md.replace(/<footer[\s\S]*?<\/footer>/gi, '');
  md = md.replace(/<header[\s\S]*?<\/header>/gi, '');
  // Meta tags
  const titleMatch = md.match(/<title[^>]*>(.*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : '';
  const descMatch = md.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i);
  const desc = descMatch ? descMatch[1].trim() : '';
  // Headings
  md = md.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '\n# $1\n');
  md = md.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '\n## $1\n');
  md = md.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '\n### $1\n');
  md = md.replace(/<h4[^>]*>(.*?)<\/h4>/gi, '\n#### $1\n');
  md = md.replace(/<h5[^>]*>(.*?)<\/h5>/gi, '\n##### $1\n');
  md = md.replace(/<h6[^>]*>(.*?)<\/h6>/gi, '\n###### $1\n');
  // Bold and italic
  md = md.replace(/<(strong|b)[^>]*>(.*?)<\/\1>/gi, '**$2**');
  md = md.replace(/<(em|i)[^>]*>(.*?)<\/\1>/gi, '*$2*');
  // Links
  md = md.replace(/<a[^>]+href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gi, '[$2]($1)');
  // Images
  md = md.replace(/<img[^>]+src=["']([^"']+)["'][^>]+alt=["']([^"']+)["'][^>]*\/?>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]+src=["']([^"']+)["'][^>]*\/?>/gi, '![]($1)');
  // Lists
  md = md.replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n');
  md = md.replace(/<\/?(ul|ol)[^>]*>/gi, '\n');
  // Tables — simplified: extract rows
  md = md.replace(/<tr[^>]*>([\s\S]*?)<\/tr>/gi, (m, row) => {
    const cells = [...row.matchAll(/<t[dh][^>]*>(.*?)<\/t[dh]>/gi)].map(c => c[1].trim());
    return `| ${cells.join(' | ')} |\n`;
  });
  md = md.replace(/<\/?table[^>]*>/gi, '\n');
  md = md.replace(/<\/?thead[^>]*>/gi, '');
  md = md.replace(/<\/?tbody[^>]*>/gi, '');
  // Code blocks
  md = md.replace(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/gi, '\n```\n$1\n```\n');
  md = md.replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`');
  // Blockquotes
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, (m, c) => 
    c.split('\n').map(l => '> ' + l).join('\n'));
  // Paragraphs and breaks
  md = md.replace(/<p[^>]*>(.*?)<\/p>/gi, '\n$1\n');
  md = md.replace(/<br\s*\/?>/gi, '\n');
  md = md.replace(/<hr\s*\/?>/gi, '\n---\n');
  // Divs — just preserve content
  md = md.replace(/<\/?div[^>]*>/gi, '\n');
  // Remove remaining tags
  md = md.replace(/<[^>]+>/g, '');
  // Decode common HTML entities
  md = md.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
         .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
         .replace(/&mdash;/g, '—').replace(/&ndash;/g, '–').replace(/&hellip;/g, '…')
         .replace(/&copy;/g, '©').replace(/&trade;/g, '™').replace(/&reg;/g, '®')
         .replace(/&sect;/g, '§').replace(/&para;/g, '¶');
  // Clean up whitespace
  md = md.replace(/\n{3,}/g, '\n\n').replace(/^\s+/gm, '').trim();
  // Add header with metadata
  const header = `# ${title || path}\n${desc ? `\n> ${desc}\n` : ''}\n---\n`;
  return header + md;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const accept = request.headers.get('Accept') || '';
    const host = url.hostname;

    // ─── Server-side bot detection ─────────────────────────────────────
    // Detect bots on EVERY request — the JS beacon doesn't fire for crawlers
    const userAgent = request.headers.get('User-Agent') || '';
    const botInfo = detectBot(userAgent);

    // Only fire beacon for page-like requests (not static assets)
    const isPageRequest = !path.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|xml|txt|json|map)$/i)
      && !path.startsWith('/api/')
      && !path.startsWith('/.well-known/');

    // Fire beacon for ALL bot visits (they don't run JS beacon).
    // For humans: only fire for non-HTML requests or when JS beacon might not fire.
    // Human pageviews are tracked by the JS beacon — don't double-count.
    if (isPageRequest && botInfo) {
      ctx.waitUntil(fireBeacon(request, host, path, botInfo));
    }

    // ─── 301 permanent redirects for trailing slash URLs ─────────────────
    // Cloudflare Pages returns 307 (temporary) by default — convert to 301
    // Skip root path, directory index pages (which need the slash)
    const DIR_INDEXES = ['/blog/', '/concepts/', '/guides/', '/vs/', '/alternatives/'];
    if (path.endsWith('/') && path !== '/' && !DIR_INDEXES.includes(path)) {
      const newPath = path.slice(0, -1) + url.search;
      return Response.redirect(new URL(newPath, url.origin).toString(), 301);
    }
    // Redirect no-slash to with-slash for directory index pages
    const DIR_NO_SLASH = ['/blog', '/concepts', '/guides', '/vs', '/alternatives'];
    if (DIR_NO_SLASH.includes(path)) {
      return Response.redirect(new URL(path + '/', url.origin).toString(), 301);
    }

    // ─── Demo runner script: serve as text/plain ─────────────────────────
    if (path === '/demo/run.py') {
      const pyRequest = new Request(new URL('/demo/run.py', url.origin), request);
      const pyResponse = await env.ASSETS.fetch(pyRequest);
      if (pyResponse.ok) {
        const pyContent = await pyResponse.text();
        return new Response(pyContent, {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Cache-Control': 'public, max-age=3600',
            'Vary': 'Accept, Accept-Encoding',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }
    }

    // ─── JSON error responses for /api/* paths ───────────────────────────
    if (path.startsWith('/api/') && !path.startsWith('/api/analytics/') && !path.startsWith('/api/openapi')) {
      const errorResponse = (status, code, message, resolution) => {
        return new Response(JSON.stringify({ error: code, message, resolution }), {
          status,
          headers: {
            'Content-Type': 'application/json',
            'Vary': 'Accept',
            'Access-Control-Allow-Origin': '*',
          },
        });
      };

      // OpenAPI spec is a real endpoint
      if (path === '/api/openapi') {
        return env.ASSETS.fetch(new Request(new URL('/openapi.json', url.origin), request));
      }

      // API endpoints not yet implemented as live handlers — return 404 (not 501)
      return errorResponse(404, 'NOT_FOUND', 'This API endpoint is not deployed. The platform is accessible via MCP server and CLI.', 'See https://mos2es.org/docs for MCP server and CLI usage, or https://mos2es.org/openapi.json for the full API spec.');
    }

    // ─── Consolidated pages: alternatives → vs ───────────────────────────
    const CONSOLIDATED = {
      '/alternatives/workera-alternatives': '/vs/workera',
      '/alternatives/worklytics-alternatives': '/vs/worklytics',
      // Concept consolidation: 24 pages → 3 (metrics, ai-evaluation, confirmation-hacking)
      // 10 metric/framework definition pages → /concepts/metrics
      '/concepts/yield': '/concepts/metrics#yield',
      '/concepts/leverage': '/concepts/metrics#leverage',
      '/concepts/token-snr': '/concepts/metrics#snr',
      '/concepts/construction': '/concepts/metrics#construction',
      '/concepts/composite-score': '/concepts/metrics',
      '/concepts/divergence': '/concepts/metrics#divergence',
      '/concepts/benchmark': '/concepts/metrics#benchmark',
      '/concepts/intervention': '/concepts/metrics#intervention',
      '/concepts/canonical-telemetry': '/concepts/metrics#canonical-telemetry',
      '/concepts/governance': '/concepts/metrics#governance',
      // 13 AI evaluation landscape pages → /concepts/ai-evaluation
      '/concepts/ai-evaluations': '/concepts/ai-evaluation',
      '/concepts/ai-agent-evaluation': '/concepts/ai-evaluation',
      '/concepts/ai-evaluator': '/concepts/ai-evaluation',
      '/concepts/ai-model-evaluation': '/concepts/ai-evaluation',
      '/concepts/ai-evaluation-frameworks': '/concepts/ai-evaluation',
      '/concepts/evaluating-ai': '/concepts/ai-evaluation',
      '/concepts/ai-evaluation-tools': '/concepts/ai-evaluation',
      '/concepts/best-ai-evaluation-tools-for-production': '/concepts/ai-evaluation',
      '/concepts/ai-evaluation-platform': '/concepts/ai-evaluation',
      '/concepts/ai-model-safety-evaluation-benchmark-continuous-testing': '/concepts/ai-evaluation',
      '/concepts/ai-evaluation-news': '/concepts/ai-evaluation',
      '/concepts/ai-compliance-standards': '/concepts/ai-evaluation',
      // confirmation-hacking-ai-evaluation → confirmation-hacking (clean URL)
      '/concepts/confirmation-hacking-ai-evaluation': '/concepts/confirmation-hacking',
      // killer-experiment → baseline-assessment (URL rename)
      '/killer-experiment': '/baseline-assessment',
    };
    if (CONSOLIDATED[path]) {
      return Response.redirect(new URL(CONSOLIDATED[path], url.origin).toString(), 301);
    }

    // ─── favicon.ico redirect to favicon.svg ─────────────────────────────
    if (path === '/favicon.ico') {
      return Response.redirect(new URL('/favicon.svg', url.origin).toString(), 301);
    }

    // ─── Well-known discovery endpoints with correct Content-Types ───────
    // Serve from inline content first (reliable), fall back to assets
    if (WELL_KNOWN_INLINE[path]) {
      const entry = WELL_KNOWN_INLINE[path];
      return new Response(entry.body, {
        status: 200,
        headers: {
          'Content-Type': entry.type,
          'Vary': 'Accept, Accept-Encoding',
          'Cache-Control': 'public, max-age=3600',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    // ─── auth.md at root ─────────────────────────────────────────────────
    if (path === '/auth.md' && WELL_KNOWN_INLINE['/auth.md']) {
      const entry = WELL_KNOWN_INLINE['/auth.md'];
      return new Response(entry.body, {
        status: 200,
        headers: {
          'Content-Type': entry.type,
          'Vary': 'Accept, Accept-Encoding',
          'Cache-Control': 'public, max-age=3600',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    // ─── Markdown content negotiation ────────────────────────────────────
    // When an agent sends Accept: text/markdown, serve the page as markdown
    if (accept.includes('text/markdown')) {
      const mdHeaders = {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Vary': 'Accept, Accept-Encoding',
        'Cache-Control': 'public, max-age=3600',
        'Content-Signal': 'search=yes, ai-input=yes',
        'Access-Control-Allow-Origin': '*',
      };
      // First try .md files for known pages
      const mdPageName = MARKDOWN_PAGES[path];
      if (mdPageName) {
        const mdRequest = new Request(new URL(`/${mdPageName}.md`, url.origin));
        const mdResponse = await env.ASSETS.fetch(mdRequest);
        if (mdResponse.ok) {
          const mdContent = await mdResponse.text();
          return new Response(mdContent, { headers: mdHeaders });
        }
        // No .md file — fetch the HTML and convert to markdown
        // Try multiple path variants the assets binding might expect
        for (const htmlPath of [`/${mdPageName}.html`, `/${mdPageName}`, mdPageName === 'index' ? '/' : `/${mdPageName}/index.html`]) {
          const htmlRequest = new Request(new URL(htmlPath, url.origin));
          const htmlResponse = await env.ASSETS.fetch(htmlRequest);
          if (htmlResponse.ok) {
            const htmlContent = await htmlResponse.text();
            if (htmlContent.includes('<html') || htmlContent.includes('<!DOCTYPE')) {
              const markdown = htmlToMarkdown(htmlContent, path);
              return new Response(markdown, { headers: mdHeaders });
            }
          }
        }
      }
      // For any other path, try HTML-to-markdown conversion
      if (path !== '/' && !path.includes('.')) {
        for (const htmlPath of [`${path}.html`, path, `${path}/index.html`]) {
          const htmlRequest = new Request(new URL(htmlPath, url.origin));
          const htmlResponse = await env.ASSETS.fetch(htmlRequest);
          if (htmlResponse.ok) {
            const htmlContent = await htmlResponse.text();
            if (htmlContent.includes('<html') || htmlContent.includes('<!DOCTYPE')) {
              const markdown = htmlToMarkdown(htmlContent, path);
              return new Response(markdown, { headers: mdHeaders });
            }
          }
        }
      }
      // Ultimate fallback: llms.txt
      const llmsRequest = new Request(new URL('/llms.txt', url.origin));
      const llmsResponse = await env.ASSETS.fetch(llmsRequest);
      if (llmsResponse.ok) {
        const llmsContent = await llmsResponse.text();
        return new Response(llmsContent, { headers: mdHeaders });
      }
    }

    // ─── Clean URL routing: strip .html extensions ───────────────────────
    let assetPath = path;
    if (path.endsWith('.html')) {
      assetPath = path.slice(0, -5); // strip .html
    }
    if (path !== '/' && !path.includes('.')) {
      // Try path as-is first (for directories with index.html)
      const directResponse = await env.ASSETS.fetch(request);
      if (directResponse.ok) return await addHeaders(directResponse, request);
      // Try with .html extension
      const htmlRequest = new Request(new URL(`${path}.html`, url.origin), request);
      const htmlResponse = await env.ASSETS.fetch(htmlRequest);
      if (htmlResponse.ok) return await addHeaders(htmlResponse, request);
      // Try subdirectory paths (e.g., /concepts/leverage → /concepts/leverage.html)
      const subHtmlRequest = new Request(new URL(`${assetPath}.html`, url.origin), request);
      const subHtmlResponse = await env.ASSETS.fetch(subHtmlRequest);
      if (subHtmlResponse.ok) return await addHeaders(subHtmlResponse, request);
    }

    // ─── Default: pass through to assets ─────────────────────────────────
    const response = await env.ASSETS.fetch(request);

    // Add Vary header to all responses
    return await addHeaders(response, request);
  },
};

async function addHeaders(response, request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const contentType = response.headers.get('Content-Type') || '';
  const isHtmlPage = contentType.includes('text/html');

  // Determine cache strategy based on content type
  let cacheControl;
  if (isHtmlPage) {
    // HTML pages: short cache, must revalidate (content changes when we deploy)
    cacheControl = 'public, max-age=300, s-maxage=3600, stale-while-revalidate=86400';
  } else if (contentType.includes('text/css') || contentType.includes('javascript') || contentType.includes('image/svg')) {
    // Static assets: long cache (immutable, versioned by deploy)
    cacheControl = 'public, max-age=31536000, immutable';
  } else if (contentType.includes('image/') || contentType.includes('font/') || contentType.includes('application/json')) {
    // Images, fonts, JSON: medium cache
    cacheControl = 'public, max-age=86400, s-maxage=604800';
  } else {
    // Default: short cache
    cacheControl = 'public, max-age=3600';
  }

  // Link headers for agent discoverability (homepage and HTML pages)
  if (isHtmlPage || (!path.includes('.') || path.endsWith('.html') || path === '/')) {
    const links = [
      '<https://mos2es.org/llms.txt>; rel="service"; type="text/plain"; title="llms.txt"',
      '<https://mos2es.org/sitemap.xml>; rel="sitemap"; type="application/xml"',
      '<https://mos2es.org/openapi.json>; rel="service-desc"; type="application/json"; title="OpenAPI"',
      '<https://mcp.mos2es.org/mcp>; rel="service"; type="application/json"; title="MCP Server"',
      '<https://mos2es.org/.well-known/agent.json>; rel="service"; type="application/json"; title="Agent Manifest"',
      '<https://mos2es.org/.well-known/agent-card.json>; rel="service"; type="application/json"; title="A2A Agent Card"',
      '<https://mos2es.org/.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"',
      '<https://mos2es.org/.well-known/ai-catalog.json>; rel="ai-catalog"; type="application/json"',
      '<https://mos2es.org/.well-known/mcp/server-card.json>; rel="service"; type="application/json"; title="MCP Server Card"',
      '<https://mos2es.org/.well-known/auth.md>; rel="service"; type="text/markdown"; title="Auth.md"',
      '<https://mos2es.org/.well-known/exchange.json>; rel="service"; type="application/json"; title="Contribution Exchange"',
      '<https://mos2es.org/crawl-control.json>; rel="service"; type="application/json"; title="Crawl Control"',
    ];

    // Inject analytics beacon into HTML pages
    if (isHtmlPage) {
      const linkHeader = links.join(', ');
      const html = await response.text();
      const modified = html.replace('</body>', '<script src="/analytics-beacon.js"></script></body>');
      return new Response(modified, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Vary': 'Accept, Accept-Encoding',
          'Cache-Control': cacheControl,
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'SAMEORIGIN',
          'Referrer-Policy': 'strict-origin-when-cross-origin',
          'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; font-src 'self'; connect-src 'self' https://mcp.mos2es.org https://www.google-analytics.com https://www.googletagmanager.com;",
          'Link': linkHeader,
        },
      });
    }

    const newResponse = new Response(response.body, response);
    newResponse.headers.set('Vary', 'Accept, Accept-Encoding');
    newResponse.headers.set('Cache-Control', cacheControl);
    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    newResponse.headers.set('X-Frame-Options', 'SAMEORIGIN');
    newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    newResponse.headers.set('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; font-src 'self'; connect-src 'self' https://mcp.mos2es.org https://www.google-analytics.com https://www.googletagmanager.com;");
    newResponse.headers.set('Link', links.join(', '));
    return newResponse;
  }

  const newResponse = new Response(response.body, response);
  newResponse.headers.set('Vary', 'Accept, Accept-Encoding');
  newResponse.headers.set('Cache-Control', cacheControl);
  newResponse.headers.set('X-Content-Type-Options', 'nosniff');
  newResponse.headers.set('X-Frame-Options', 'SAMEORIGIN');
  newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  newResponse.headers.set('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; font-src 'self'; connect-src 'self' https://mcp.mos2es.org https://www.google-analytics.com https://www.googletagmanager.com;");
  return newResponse;
}
