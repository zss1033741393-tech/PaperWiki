# PaperWiki Project Plan

## Goal

Build a paper-learning system in which discovery, deep reading, and knowledge deposition can run independently or as a complete pipeline. Preserve provenance, keep recommendations explainable, and never overwrite human notes silently.

## Architecture

### Discover papers

Use multi-source retrieval, normalize identifiers, deduplicate results, and score candidates. Produce machine-readable records and a human-readable shortlist. Discovery ends after selection and does not require downloading or reading.

| Signal | Weight |
| --- | ---: |
| Topic relevance | 30% |
| Venue/publication quality | 20% |
| Citation impact | 15% |
| Recency | 15% |
| Code/reproducibility | 10% |
| Author/research continuity | 5% |
| Novelty/community interest | 5% |

Normalize components to `[0, 1]`. Expose component scores, evidence coverage, total score, and inclusion reasons. Missing citation data must not mean zero quality.

### Read a paper

Accept a direct URL, DOI, arXiv ID, local PDF, or discovery record. Preserve the source, invoke `paper-craft-skills`, and emit a report plus structured reading fields. Discovery metadata is optional.

### Deposit knowledge

Accept a PaperWiki report, another report, or user notes. Resolve a stable paper ID, merge a paper page, update concept/method/dataset/topic pages and indexes, and append an operation log. Generated and human-confirmed content remain distinguishable. Re-ingestion is idempotent.

## Data and storage

Use Markdown, YAML frontmatter, Obsidian wikilinks, and Git for v1. Store immutable sources under `raw/`, reports under `reports/`, and distilled pages under `wiki/`. Use DOI as canonical ID, then arXiv ID, then a normalized-title hash.

```text
discovered -> shortlisted -> queued -> reading -> reviewed -> deposited -> revisited
```

Skipping stages is valid. A supplied PDF may begin at `reading`; existing notes may begin at `reviewed`.

## Delivery milestones

1. Foundation: three skills, shared schema, ranking helper, wiki rules, and tests.
2. Provider integration: paper-search-mcp, arXiv, Semantic Scholar, PDF acquisition, retries, provenance.
3. Paper Craft integration: install or vendor paper-craft-skills and map its output to the shared record.
4. Knowledge workflows: idempotent ingest, wikilinks, indexes, topic synthesis, conflicts, Obsidian views.
5. Product layer: UI or command orchestrator, job state, optional semantic index, deployment.

## Acceptance criteria

- Each skill succeeds without output from the previous skill.
- Duplicate DOI/arXiv records converge on one canonical paper.
- Ranking explains every score and unavailable evidence.
- Re-depositing creates no duplicate and preserves human notes.
- A related second paper updates shared concepts and topic navigation.
- Rate limits, missing PDFs, retractions, and conflicts produce recoverable errors.

## Initial dependencies

- Discovery: `openags/paper-search-mcp`, Semantic Scholar, arXiv; DeerFlow literature review is optional.
- Reading: `Wm78gh/paper-craft-skills`.
- Knowledge: `infranodus/skills/skill-llm-wiki` and `kepano/obsidian-skills` as references.

