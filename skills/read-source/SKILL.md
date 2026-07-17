---
name: read-source
description: Use when the user supplies a paper URL, DOI, arXiv ID, local PDF, title, discovery record, engineering blog post, documentation page, or GitHub repository and asks to read, summarize, explain, review, or study that single source in depth.
---

# Read Source

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. Do not require discovery metadata. `python paperwiki.py read <input> --report-slug <slug>` detects the source type: arXiv/DOI/PDF → paper; github.com → github; other URLs → blog/docs.
2. Resolve metadata and accessible full text. Preserve original input, resolved URL, retrieval time, and source path.
3. **Papers** follow the unchanged deep-read path: invoke `vendor/paper-craft-skills/skills/paper-analyzer/SKILL.md`; evidence cites page/section/figure. **Blogs and docs**: read the full text; evidence cites section/heading. **Repos**: read README, docs, and key entry points; evidence cites file paths.
4. Choose the official abbreviation or repo name as the lowercase slug. Write `reports/<slug>/analysis.json`. Non-paper sources may omit `experiments`, `reproducibility`, and `datasets` (the relaxed gate is enforced by finalize; see `references/analysis.schema.json`). Include a `tools` list when the source centers on named frameworks or tools; deposit links them into `wiki/tools/`. Include `source_type` in the analysis.
5. Run `python paperwiki.py finalize reports/<slug>/report.md reports/<slug>/analysis.json` to generate the readable report and update `record.json`.
6. Separate source claims, interpretation, and user notes. Keep the canonical artifact set `report.md`, `report.html`, `analysis.json`, `record.json`. Set `reviewed` only after user confirmation.

## Completion Gate

Before claiming a report is complete or committing it:

1. Rebuild `report.html` from the matching `report.md`; never repair rendered formulas by editing HTML directly.
2. Run `python skills/read-source/scripts/verify_report.py reports/<paper-slug>/report.md`. Any nonzero exit blocks completion. The command verifies that every Markdown math span survives unchanged in HTML and that no renderer placeholder remains.
3. Run the relevant regression tests, then the full test suite.
4. When browser access is available, inspect representative inline and display formulas. Confirm there are no `.katex-error` nodes, visible raw `$$` delimiters, or horizontal page overflow.

If a check fails, fix the Markdown source or shared renderer, regenerate the HTML, and repeat the entire gate. A visual spot check alone does not replace the deterministic verifier.

## Guardrails

- Flag inaccessible pages, paywalls, OCR uncertainty, and unsupported claims.
- Never invent venue, citation, experiment, benchmark, or code information.
- Treat authored `report.md` prose as canonical long-form content; do not replace it with a thinner summary when rerunning `finalize`.
- Do not automatically invoke `deposit-paper-knowledge`.
- A separate `deepen-reading` skill runs a complementary PaperForge reading pass over an existing report. Offer it as a follow-up; do not invoke it automatically.
