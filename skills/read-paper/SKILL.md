---
name: read-paper
description: Acquire and deeply explain one academic paper, producing a structured, visual learning report. Use when the user supplies a paper URL, DOI, arXiv ID, local PDF, title, or discovery record and asks to read, summarize, explain, review, or study it. Run independently of paper discovery and do not deposit the result unless requested.
---

# Read Paper

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. Do not require discovery metadata.
2. Resolve metadata and accessible full text. Preserve original input, resolved URL, retrieval time, and source path.
3. Invoke `vendor/paper-craft-skills/skills/paper-analyzer/SKILL.md` for deep analysis. Use paper-summary, paper-mindmap, paper-comic, or paper-deck when the user requests that output. Report a missing dependency rather than pretending it ran.
4. Write the analysis as JSON matching `references/analysis.schema.json`, including page/section/figure evidence. Run `python paperwiki.py finalize <report.md> <analysis.json>` to generate the readable Markdown and HTML report and update the record.
5. Separate paper claims, interpretation, and user notes. Cite page, section, figure, or equation locations when available.
6. Save under `reports/` inside PaperWiki. Set `reviewed` only after user confirmation.

## Guardrails

- Flag inaccessible appendices, missing pages, OCR uncertainty, and unsupported claims.
- Never invent venue, citation, experiment, or code information.
- Do not automatically invoke `deposit-paper-knowledge`.
