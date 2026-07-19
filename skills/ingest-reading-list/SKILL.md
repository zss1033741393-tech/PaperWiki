---
name: ingest-reading-list
description: Use when the user asks to import, sync, refresh, or track a curated reading list (an awesome list or similar link collection) into PaperWiki, or asks what is new upstream or how far their study of a list has progressed.
---

# Ingest Reading List

## Workflow

1. Accept a GitHub repo URL, raw README URL, or local README path. Run `python paperwiki.py ingest <source> --list-slug <slug>`; the slug defaults to the repo name.
2. The parser maps `##`/`###` headings to `section_path` and `- [Title](url) — description` lines to entries; the `Contents` section is skipped and badges are stripped from descriptions. Entries conform to `references/reading-list.schema.json`.
3. Identity is `arxiv:<id>` > `doi:<doi>` > `url:<sha256-12>` of the normalized URL, matching the pipeline-wide rule; arXiv entries later merge with the paper pipeline automatically.
4. Source types come from host heuristics (`paper | github | blog | docs | other`); report obvious misclassifications instead of silently accepting them.
5. Re-running the same command is the update mechanism: report the printed diff (added / removed-upstream / changed) and unparsed lines to the user. Never edit `status` fields during ingest.
6. Use `python paperwiki.py mark <slug> <source_id ...> --status <status> [--reason <text>]` to move entries through `unread → queued → skimmed → studied → deposited`; `blocked` requires a reason.

## Guardrails

- Never delete entries that disappeared upstream; they stay flagged `removed_upstream`.
- Unparsed lines go to the diff summary, not to the void; surface them.
- Do not start reading or depositing content unless the user asks; ingestion is bookkeeping only.
