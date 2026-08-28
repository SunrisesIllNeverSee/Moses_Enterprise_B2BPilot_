# AGENTS.md

## Upsilon Architecture Context (2026-08-28)

**Architecture:** `MO§ES → Upsilon → SigRank | SignalAF`

- **Upsilon** = measurement engine / enterprise product (the engine that measures)
- **SigRank** = public leaderboard / benchmark / proof surface (live at signalaf.com)
- **SignalAF** = public distribution / platform brand
- **Yield (Υ)** = metric inside Upsilon: `(cache_read × output) / input²`
- **MO§ES™** = governance framework / methodology

**Owner clarification (2026-08-28):** The primary change is the Upsilon pilot.
agent-universe and sigrank-app changes are minimal — just pointing toward the
pilot and establishing architecture context. All repos get this context so they
understand where it came from and don't try rewriting everything every time.

**Do NOT:**
- Rename package/repo/CLI names (sigrank-app, sigrank-mcp, npx sigrank) — these are technical identifiers
- Rename "SigRank" where it means the public leaderboard/benchmark
- Conflate "Upsilon" (product) with "Yield" (metric) — they are different things
- Mass-rewrite historical/archive content to conform to new branding
- Change patent claims without legal review

**Preserved:**
- `npx sigrank` CLI command
- `sigrank` npm package name
- `sigrank-app`, `sigrank-mcp` repo names
- All URLs (signalaf.com, sigeconomy.com, mos2es.org, signomy.xyz)
- "SigRank leaderboard/board/ranks" references
- Historical and archive content

**Canon source:** Search Authority (commit 790d403). Load canon context before
modifying product definitions, metrics, or terminology:
```bash
export SEARCH_AUTHORITY_PATH="${SEARCH_AUTHORITY_PATH:-$HOME/Developer/_control/search-authority}"
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context sigrank
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context upsilon
```
