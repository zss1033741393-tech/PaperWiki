# PaperWiki Agent Rules

## Paper Report Completion Gate

When changing a paper report, `finalize`, or Markdown-to-HTML rendering:

- Preserve an authored `report.md` body; do not replace it with a thinner generated summary.
- Rebuild `report.html` from its matching `report.md`.
- Run `python skills/read-paper/scripts/verify_report.py <report.md-or-directory>` for every changed report. A nonzero exit blocks completion.
- Run the relevant regression tests, followed by the full test suite before committing.
- When browser access is available, inspect representative display and inline formulas and confirm there are no `.katex-error` nodes, visible raw `$$` delimiters, or horizontal overflow outside the formula container.
- Never set `reviewed` or claim review completion without explicit human confirmation.

Do not bypass a failing formula check with manual HTML edits. Fix the Markdown source or shared renderer, regenerate the HTML, and rerun the gate.
