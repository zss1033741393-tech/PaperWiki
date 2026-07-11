---
name: discover-papers
description: Find, normalize, deduplicate, and transparently rank academic papers for a research direction. Use when the user asks for recent, influential, high-quality, high-score, seminal, or worthwhile papers, a reading list, related papers, or a literature shortlist. Stop after discovery unless the user also asks to read or deposit selected papers.
---

# Discover Papers

## Workflow

1. Confirm or infer topic, time window, count, and field. Default to 10 results from the last 24 months; add seminal older work when useful.
2. Search at least two suitable academic sources. Run `python paperwiki.py discover "<topic>" --limit <N>` for the built-in arXiv, Semantic Scholar, and Crossref path. Prefer `vendor/paper-search-mcp` when the requested domain needs its broader providers.
3. Normalize results to `references/paper-record.schema.json`; preserve sources and retrieval times.
4. Deduplicate by DOI, arXiv ID, then normalized title. Merge evidence without discarding conflicts.
5. Use the CLI scoring output, or score existing normalized records with `scripts/score_papers.py`. Read `references/ranking.md` before changing weights.
6. Return `must-read`, `recommended`, `candidate`, and `watch` groups with components, missing evidence, and inclusion reasons.
7. Save records when a project directory exists. Do not download, analyze, or deposit unless requested.

## Guardrails

- Do not equate citations with quality or treat missing citations as zero.
- Flag retractions, withdrawals, non-peer-reviewed status, and metadata conflicts.
- Prefer DOI, arXiv, and publisher evidence over secondary commentary.
