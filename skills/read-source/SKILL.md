---
name: read-source
description: Use when the user supplies a paper, URL, DOI, arXiv ID, local PDF, engineering blog, documentation page, or GitHub repository and asks for one standalone in-depth report.
---

# Read Source

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. `python paperwiki.py read <input> --report-slug <slug>` detects papers, GitHub repositories, blogs, and docs.
2. Resolve metadata and accessible full text. Preserve original input, canonical URL, retrieval time, and source path.
3. Read the complete relevant source. Papers cite page/section/figure/table; blogs and docs cite document-absolute H2 order plus paragraph/list/table positions; repositories cite README/docs/code paths and symbols.
4. Use an official abbreviation or unambiguous organization-prefixed slug. Two sources with the same title must not share a report directory.
5. Write the canonical four-file set: `report.md`, `report.html`, `analysis.json`, and `record.json`.
6. Run `python paperwiki.py finalize reports/<slug>/report.md reports/<slug>/analysis.json`. Finalize preserves an authored report body and only normalizes frontmatter, record data, and rendered HTML.
7. Keep `human_confirmed: false`; set reviewed state only after explicit user confirmation.

## Report content

Use neutral source terminology for blogs, docs, and repositories; do not label them as papers or invent experiments. A standalone report should contain:

- 来源信息与阅读范围
- 问题与背景
- 论证结构
- 关键观点与证据
- 核心概念与方法
- 局限与适用边界
- 对主题的贡献
- 与其他来源的关系
- User notes

Every key claim needs a deterministic locator. Clearly label source claims, synthesis, and open inference.

## Topic-bundle fields

When the report is selected by a `study-topic` bundle, `analysis.json` must additionally contain non-empty:

- `evidence`
- `topic_contribution`
- `relations`

The topic record binds the final deposited `report.md` SHA-256. Therefore finalize and deposit the standalone report before recording that digest in the topic synthesis.

## Completion Gate

Before claiming a report complete or committing it:

1. Rebuild `report.html` from matching `report.md`; never repair rendered HTML manually.
2. Run `python skills/read-source/scripts/verify_report.py reports/<slug>/report.md`. Any nonzero exit blocks completion.
3. Run relevant regression tests, followed by the full test suite.
4. When browser access is available, inspect representative content and formulas. Confirm zero `.katex-error` nodes, no visible raw `$$`, and no horizontal page overflow.

If a gate fails, fix Markdown or the shared renderer, regenerate HTML, and repeat the gate. Preserve authored `report.md` prose; do not replace it with a thinner generated summary. Do not automatically deposit a standalone report unless the requested workflow includes deposit.
