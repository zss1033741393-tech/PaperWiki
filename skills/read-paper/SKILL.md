---
name: read-paper
description: Use when the user supplies a paper URL, DOI, arXiv ID, local PDF, title, or discovery record and asks to read, summarize, explain, review, or study one academic paper.
---

# Read Paper

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. Do not require discovery metadata.
2. Resolve metadata and accessible full text. Preserve original input, resolved URL, retrieval time, and source path.
3. Invoke `vendor/paper-craft-skills/skills/paper-analyzer/SKILL.md` for deep analysis. Use paper-summary, paper-mindmap, paper-comic, or paper-deck when the user requests that output. Report a missing dependency rather than pretending it ran.
4. Choose the paper's official abbreviation when one exists and normalize it to a lowercase ASCII slug. Run `python paperwiki.py read <paper> --report-slug <official-abbreviation>`; omit `--report-slug` only when a concise title-derived slug is appropriate.
5. Write the analysis to `reports/<paper-slug>/analysis.json` matching `references/analysis.schema.json`, including page/section/figure evidence. Run `python paperwiki.py finalize reports/<paper-slug>/report.md reports/<paper-slug>/analysis.json` to generate a report from the initial scaffold or preserve an already authored report body, then rebuild HTML and synchronize the complete analysis into `record.json`.
6. Separate paper claims, interpretation, and user notes. Cite page, section, figure, or equation locations when available.
7. Keep the canonical artifact set `report.md`, `report.html`, `analysis.json`, and `record.json` inside `reports/<paper-slug>/`. Set `reviewed` only after user confirmation.

## Guardrails

- Flag inaccessible appendices, missing pages, OCR uncertainty, and unsupported claims.
- Never invent venue, citation, experiment, or code information.
- Treat authored `report.md` prose as canonical long-form content; do not replace it with a thinner summary when rerunning `finalize`.
- Do not automatically invoke `deposit-paper-knowledge`.
