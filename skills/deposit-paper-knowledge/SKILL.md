---
name: deposit-paper-knowledge
description: Convert a paper report or user-authored reading notes into an idempotent, linked Markdown and Obsidian knowledge base. Use when the user asks to archive, deposit, preserve, organize, connect, or add learned paper content to PaperWiki, including reports not produced by read-paper. Do not require discovery or automatic paper reading.
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

## Idempotency

- Re-running the same input updates one paper page.
- Normalize DOI case and URL variants; ignore arXiv version suffix for identity but retain source version.
- Retain conflicting sourced values and add a resolution task.

