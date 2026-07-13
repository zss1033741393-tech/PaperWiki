---
name: deposit-paper-knowledge
description: Use when the user asks to archive, deposit, preserve, organize, connect, or add a paper report or reading notes to PaperWiki, including reports not produced by read-paper.
---

# Deposit Paper Knowledge

## Workflow

1. Accept a PaperWiki report, another report, or user notes. Do not require discovery or reading records.
2. Read `references/wiki-schema.md` and normalize available metadata against `references/paper-record.schema.json`.
3. Resolve identity by DOI, arXiv ID, then normalized-title SHA-256 prefix. Search before creating files.
4. Preserve raw input when appropriate. Create or merge the page under `wiki/papers/`.
5. Extract concepts, methods, datasets, authors, and topics. Add reciprocal Obsidian wikilinks without duplication.
6. Preserve human-authored sections verbatim. Mark uncertain generated material as draft; never silently replace conflicts.
7. Update `index.md`, affected topics, and `log.md`. Set `deposited` only after validation.
8. For a PaperWiki report, use the official-abbreviation directory and run `python paperwiki.py deposit <vault>/reports/<paper-slug>/report.md --root <vault>`. The sibling `record.json` is authoritative; legacy same-stem JSON remains accepted. After deposition, run `python paperwiki.py recommend --topic "<topic>" --root <vault>` when the user asks for the next reading direction.

## Idempotency

- Re-running the same input updates one paper page.
- Normalize DOI case and URL variants; ignore arXiv version suffix for identity but retain source version.
- Retain conflicting sourced values and add a resolution task.

## Obsidian companion skills (vendored, optional)

The wiki is Obsidian-flavored Markdown: entity and paper relations use **short-name** `[[wikilinks]]` (Obsidian's default "shortest path" format), while source reports use vault-qualified links such as `[[reports/latentmas/report|LatentMAS report]]` because every paper report is named `report.md`. It also uses `[!summary]` callouts and YAML frontmatter properties. Open the repository root as the Obsidian vault so both `wiki/` notes and `reports/` sources resolve and appear in graph view. The pinned `vendor/obsidian-skills` (by kepano) provides optional companions:

- `obsidian-markdown` — authoritative Obsidian Flavored Markdown (wikilinks, callouts, embeds, properties) when hand-editing wiki pages.
- `obsidian-cli` — read/search/manage the vault (notes, tasks, properties) and drive Obsidian from the command line.
- `json-canvas` — render the paper ↔ concept ↔ method graph as an Obsidian `.canvas`.
- `obsidian-bases` — build `.base` database views over the wiki (e.g., all `must-read` papers grouped by topic).

Install as a Claude Code plugin (`/plugin marketplace add kepano/obsidian-skills` → `/plugin install obsidian@obsidian-skills`) or `git submodule update --init vendor/obsidian-skills`. These are optional — core deposit emits plain Obsidian-compatible Markdown without them.
