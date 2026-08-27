// MO§ES™ promo worker — static assets + AEO enhancements
// Handles: clean URLs, markdown content negotiation, JSON errors, Vary header

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
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const accept = request.headers.get('Accept') || '';

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
    if (path.startsWith('/api/')) {
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

      // API endpoints not yet implemented as live handlers — return informative JSON
      return errorResponse(501, 'NOT_IMPLEMENTED', 'This API endpoint is defined in the OpenAPI spec but not yet deployed as a live handler. The platform is accessible via MCP server and CLI.', 'See https://mos2es.org/docs for MCP server and CLI usage, or https://mos2es.org/openapi.json for the full API spec.');
    }

    // ─── Markdown content negotiation ────────────────────────────────────
    if (accept.includes('text/markdown') && MARKDOWN_PAGES[path]) {
      const pageName = MARKDOWN_PAGES[path];
      // Try to serve a .md file if it exists, otherwise convert HTML to simple text
      const mdRequest = new Request(new URL(`/${pageName}.md`, url.origin), request);
      const mdResponse = await env.ASSETS.fetch(mdRequest);
      if (mdResponse.ok) {
        const mdContent = await mdResponse.text();
        return new Response(mdContent, {
          headers: {
            'Content-Type': 'text/markdown; charset=utf-8',
            'Vary': 'Accept, Accept-Encoding',
            'Cache-Control': 'public, max-age=3600',
          },
        });
      }
      // No .md file — return a markdown summary from llms.txt content
      const llmsRequest = new Request(new URL('/llms.txt', url.origin), request);
      const llmsResponse = await env.ASSETS.fetch(llmsRequest);
      if (llmsResponse.ok) {
        const llmsContent = await llmsResponse.text();
        return new Response(llmsContent, {
          headers: {
            'Content-Type': 'text/markdown; charset=utf-8',
            'Vary': 'Accept, Accept-Encoding',
            'Cache-Control': 'public, max-age=3600',
          },
        });
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
      if (directResponse.ok) return addHeaders(directResponse, request);
      // Try with .html extension
      const htmlRequest = new Request(new URL(`${path}.html`, url.origin), request);
      const htmlResponse = await env.ASSETS.fetch(htmlRequest);
      if (htmlResponse.ok) return addHeaders(htmlResponse, request);
      // Try subdirectory paths (e.g., /concepts/leverage → /concepts/leverage.html)
      const subHtmlRequest = new Request(new URL(`${assetPath}.html`, url.origin), request);
      const subHtmlResponse = await env.ASSETS.fetch(subHtmlRequest);
      if (subHtmlResponse.ok) return addHeaders(subHtmlResponse, request);
    }

    // ─── Default: pass through to assets ─────────────────────────────────
    const response = await env.ASSETS.fetch(request);

    // Add Vary header to all responses
    return addHeaders(response, request);
  },
};

function addHeaders(response, request) {
  const newResponse = new Response(response.body, response);
  const url = new URL(request.url);
  const path = url.pathname;

  newResponse.headers.set('Vary', 'Accept, Accept-Encoding');
  newResponse.headers.set('X-Content-Type-Options', 'nosniff');
  newResponse.headers.set('X-Frame-Options', 'SAMEORIGIN');
  newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  newResponse.headers.set('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; font-src 'self'; connect-src 'self' https://mcp.mos2es.org https://www.google-analytics.com https://www.googletagmanager.com;");

  // Link headers for agent discoverability (homepage and HTML pages)
  const isHtmlPage = !path.includes('.') || path.endsWith('.html') || path === '/';
  if (isHtmlPage) {
    const links = [
      '<https://mos2es.org/llms.txt>; rel="service"; type="text/plain"; title="llms.txt"',
      '<https://mos2es.org/sitemap.xml>; rel="sitemap"; type="application/xml"',
      '<https://mos2es.org/openapi.json>; rel="service-desc"; type="application/json"; title="OpenAPI"',
      '<https://mcp.mos2es.org/mcp>; rel="service"; type="application/json"; title="MCP Server"',
    ];
    newResponse.headers.set('Link', links.join(', '));
  }

  return newResponse;
}
