# AGENTS.md — Worker

## Context7 MCP — REQUIRED before writing library code

This worker writes code against external libraries. Before using a library API
that may have changed since training data cutoff, query Context7 to verify
the current pattern:

1. resolve-library-id — find the library (e.g. "Cloudflare Workers", "Supabase")
2. query-docs — ask the specific question (e.g. "KV write limits free tier")

Key libraries in this stack:
- Cloudflare Workers: /websites/developers_cloudflare_workers
- Cloudflare KV: /llmstxt/developers_cloudflare_kv_llms_txt
- Supabase: /supabase/supabase
- Hono: /websites/hono_dev

Do not rely on training data for library APIs. Do not call more than 3 times
per question.
