# Prompt Handoff — Next Session

## Context

You are continuing work on the MO§ES™ enterprise B2B pilot. The previous session consolidated 24 concept pages into 3, aligned metric formulas with the owner-approved canon, and committed everything (`862dfc2`).

Full handoff: `_workspace/handoffs/2026-09-02-b2b-pilot-handoff.md`
Scratch notes: `_workspace/scratch/business-notes.md`

## Immediate priorities (in order)

### 1. Deploy the promo worker

The 22 new 301 redirects for old concept URLs are committed but NOT deployed. Old concept URLs will 404 until deploy.

```bash
cd ~/Developer/active/b2bpilot/Moses_Enterprise_B2BPilot_/_workers/promo-worker
wrangler deploy
```

### 2. GSC sitemap resubmit + index push

After deploy, push the new URLs to Google:

```bash
export GSC_SA_KEY=~/.config/sigrank/gsc-sa.json
cd ~/Developer/active/SigRank-repos/scripts/gsc
node gsc.mjs sitemaps:submit
node gsc.mjs index https://mos2es.org/concepts/metrics https://mos2es.org/concepts/ai-evaluation https://mos2es.org/concepts/confirmation-hacking
node gsc.mjs check:index --push
```

### 3. Rename killer-experiment.html → baseline-assessment.html

The content already says "Baseline Assessment" but the URL is still `/killer-experiment`. Rename the file, add a 301 redirect in the promo worker, update all internal links, sitemap, and llms.txt.

### 4. Update MCP worker + demo site formulas to canon

The MCP worker (`_workers/mcp-worker/src/index.js`) and demo site (`_02_demo-website/`) still reference old metric formulas. Update to owner-approved canon:

- Yield: `(R × O) / I²`
- Leverage: `R / I`
- SNR: `O / (I + O)`
- Add Velocity, 10xDEV, Scale V
- Remove Composite Score/ODI references

Load canon context first:
```bash
python3 ~/Developer/_control/search-authority/canon_cli.py context upsilon
python3 ~/Developer/_control/search-authority/canon_cli.py context sigrank
```

## Before making changes

- Read `AGENTS.md` in the repo root
- Load canon context before touching metrics, formulas, or product definitions
- Run `git pull origin main` to get the latest
- Don't change metric formulas without canon context
- Don't reintroduce old pricing or "Killer Experiment" language
- Don't add more pages — we just consolidated
