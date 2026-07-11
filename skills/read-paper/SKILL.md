---
name: read-paper
description: Acquire and deeply explain one academic paper, producing a structured, visual learning report. Use when the user supplies a paper URL, DOI, arXiv ID, local PDF, title, or discovery record and asks to read, summarize, explain, review, or study it. Run independently of paper discovery and do not deposit the result unless requested.
---

# Read Paper

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. Do not require discovery metadata.
2. Resolve metadata and accessible full text. Preserve original input, resolved URL, retrieval time, and source path.
3. Invoke the installed `paper-craft-skills` workflow for deep analysis and requested visuals. Report a missing dependency rather than pretending it ran.
4. Produce a readable report and structured question, contributions, method, experiments, findings, limitations, reproducibility, concepts, and open questions.
5. Separate paper claims, interpretation, and user notes. Cite page, section, figure, or equation locations when available.
6. Save under `reports/` inside PaperWiki. Set `reviewed` only after user confirmation.

## Guardrails

- Flag inaccessible appendices, missing pages, OCR uncertainty, and unsupported claims.
- Never invent venue, citation, experiment, or code information.
- Do not automatically invoke `deposit-paper-knowledge`.

